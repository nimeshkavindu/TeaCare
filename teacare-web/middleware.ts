import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // 1. Read the "Badge" (Cookies) from the user's browser
  const token = request.cookies.get('token')?.value
  const role = request.cookies.get('role')?.value
  const { pathname } = request.nextUrl

  // 2. Scenario: User hits the root "/" -> Send to Login
  if (pathname === '/') {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // 3. Scenario: User tries to access Admin Panel
  if (pathname.startsWith('/admin')) {
    // Check if they are logged in AND are an Admin
    if (!token || role !== 'admin') {
      // If not, kick them to login
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }

  // 4. Scenario: User tries to access Researcher Dashboard
  if (pathname.startsWith('/dashboard')) {
    if (!token || role !== 'researcher') {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }

  // 5. If specific authentication pages (login/register) are accessed while logged in
  if (pathname.startsWith('/login') || pathname.startsWith('/register')) {
     if (token && role === 'admin') {
        return NextResponse.redirect(new URL('/admin', request.url))
     }
     if (token && role === 'researcher') {
        return NextResponse.redirect(new URL('/dashboard', request.url))
     }
  }

  // Allow the request to proceed
  return NextResponse.next()
}

// Configure which paths the middleware runs on
export const config = {
  matcher: [
    '/',
    '/admin/:path*', 
    '/dashboard/:path*',
    '/login',
    '/register'
  ],
}