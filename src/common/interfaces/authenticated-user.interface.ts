export interface JwtPayload {
  sub: string; // User ID
  email: string;
  role: string; // e.g. AUTHORITY, INTERN
  permissions: string[];
  sessionId?: string;
  iat?: number;
  exp?: number;
}

export interface AuthenticatedUser {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
  permissions: string[];
  authorityId?: string;
  internId?: string;
  sessionId?: string;
}
