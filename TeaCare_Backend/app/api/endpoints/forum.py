from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
import shutil
import uuid
import os

from app.core.database import get_db
from app.models.sql_models import ForumPost, ForumComment, PostVote, PostReport, User, SystemLog
from app.schemas.dtos import CommentRequest, VoteRequest

router = APIRouter()

# --- HELPER: LOGGING ---
def log_event(db: Session, level: str, source: str, message: str):
    try:
        new_log = SystemLog(level=level, source=source, message=message)
        db.add(new_log)
        db.commit()
    except Exception as e:
        print(f"Logging failed: {e}")

# ==========================================
# 1. POST MANAGEMENT
# ==========================================

@router.post("/posts")
def create_post(
    user_id: int = Form(...),
    author_name: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form("General"),
    file: UploadFile = File(None), 
    db: Session = Depends(get_db)
):
    # 1. Get User Role for Badge
    user = db.query(User).filter(User.user_id == user_id).first()
    role = user.role if user else "Farmer"

    # 2. Handle Image
    image_path = None
    if file:
        ext = os.path.splitext(file.filename)[1]
        file_location = f"uploads/{uuid.uuid4()}{ext}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        image_path = file_location

    # 3. Save
    new_post = ForumPost(
        user_id=user_id,
        author_name=author_name,
        author_role=role,
        title=title,
        content=content,
        category=category,
        image_url=image_path, 
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        score=0,
        views=0,
        comment_count=0
    )
    db.add(new_post)
    db.commit()
    
    log_event(db, "SUCCESS", "Forum", f"New {category} post by {author_name}")
    return {"message": "Post created"}

@router.get("/posts")
def get_posts(
    sort: str = "newest",
    filter_by: str = "all",
    search: str = "",
    user_id: int = None,
    db: Session = Depends(get_db)
):
    query = db.query(ForumPost)

    # A. Search
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(ForumPost.title.ilike(search_term), ForumPost.content.ilike(search_term)))

    # B. Filters
    if filter_by == "my_posts" and user_id:
        query = query.filter(ForumPost.user_id == user_id)
    elif filter_by == "category_alert":
        query = query.filter(ForumPost.category == "Disease Alert")

    # C. Sorting
    if sort == "popular":
        query = query.order_by(ForumPost.score.desc())
    else:
        query = query.order_by(ForumPost.post_id.desc())

    posts = query.all()
    
    # D. Attach Vote Status AND Real Comment Count
    results = []
    for p in posts:
        user_vote = 0
        if user_id:
            vote_record = db.query(PostVote).filter(PostVote.post_id == p.post_id, PostVote.user_id == user_id).first()
            if vote_record:
                user_vote = vote_record.vote_type
        
        real_comment_count = db.query(ForumComment).filter(ForumComment.post_id == p.post_id).count()

        post_dict = p.__dict__.copy()
        if "_sa_instance_state" in post_dict: del post_dict["_sa_instance_state"]
        
        post_dict['user_vote'] = user_vote
        post_dict['comment_count'] = real_comment_count
        
        if filter_by == "unanswered" and real_comment_count > 0:
            continue

        results.append(post_dict)

    return results

@router.get("/posts/{post_id}")
def get_single_post(post_id: int, user_id: int = None, db: Session = Depends(get_db)):
    post = db.query(ForumPost).filter(ForumPost.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Calculate Vote Status
    user_vote = 0
    if user_id:
        vote_record = db.query(PostVote).filter(PostVote.post_id == post_id, PostVote.user_id == user_id).first()
        if vote_record:
            user_vote = vote_record.vote_type

    post_dict = post.__dict__.copy()
    if "_sa_instance_state" in post_dict: del post_dict["_sa_instance_state"]
    post_dict['user_vote'] = user_vote
    
    return post_dict

@router.delete("/posts/{post_id}")
def delete_own_post(post_id: int, user_id: int, db: Session = Depends(get_db)):
    post = db.query(ForumPost).filter(ForumPost.post_id == post_id).first()
    if not post: raise HTTPException(status_code=404, detail="Post not found")

    # Security Check
    if post.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own posts")

    # Cleanup
    db.query(PostVote).filter(PostVote.post_id == post_id).delete()
    db.query(ForumComment).filter(ForumComment.post_id == post_id).delete()
    db.query(PostReport).filter(PostReport.post_id == post_id).delete()
    
    db.delete(post)
    db.commit()
    return {"message": "Post deleted"}

# ==========================================
# 2. INTERACTION (Voting & Comments)
# ==========================================

@router.post("/posts/{post_id}/vote")
def vote_post(post_id: int, vote: VoteRequest, db: Session = Depends(get_db)):
    post = db.query(ForumPost).filter(ForumPost.post_id == post_id).first()
    if not post: raise HTTPException(status_code=404, detail="Post not found")

    # Check existing vote
    existing_vote = db.query(PostVote).filter(PostVote.post_id == post_id, PostVote.user_id == vote.user_id).first()

    if existing_vote:
        # If user is changing vote (e.g. Up -> Down)
        post.score -= existing_vote.vote_type
        
        if vote.vote_type == 0:
            # Removing vote completely
            db.delete(existing_vote)
        else:
            # Updating vote
            existing_vote.vote_type = vote.vote_type
            post.score += vote.vote_type
    else:
        # New Vote
        if vote.vote_type != 0:
            new_vote = PostVote(user_id=vote.user_id, post_id=post_id, vote_type=vote.vote_type)
            db.add(new_vote)
            post.score += vote.vote_type

    db.commit()
    return {"new_score": post.score}

@router.post("/comments")
def create_comment(comment: CommentRequest, db: Session = Depends(get_db)):
    # 1. Create Comment
    new_comment = ForumComment(
        post_id=comment.post_id,
        user_id=comment.user_id,
        author_name=comment.author_name,
        content=comment.content,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    db.add(new_comment)
    
    # 2. Update Post Count
    post = db.query(ForumPost).filter(ForumPost.post_id == comment.post_id).first()
    if post:
        post.comment_count += 1 
        
    db.commit()
    return {"message": "Comment added"}

@router.get("/posts/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db)):
    return db.query(ForumComment).filter(ForumComment.post_id == post_id).all()

# ==========================================
# 3. REPORTING (Moderation)
# ==========================================

@router.post("/posts/{post_id}/report")
def report_post(post_id: int, user_id: int = Form(...), reason: str = Form(...), db: Session = Depends(get_db)):
    # Check if this user already reported this post
    existing = db.query(PostReport).filter(PostReport.post_id == post_id, PostReport.user_id == user_id).first()
    if existing:
        return {"message": "You have already reported this post."}

    new_report = PostReport(
        post_id=post_id, 
        user_id=user_id, 
        reason=reason, 
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    db.add(new_report)
    db.commit()
    
    log_event(db, "WARNING", "Forum", f"Post {post_id} reported by User {user_id}")
    return {"message": "Report submitted"}