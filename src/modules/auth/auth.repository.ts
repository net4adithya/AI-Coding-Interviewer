// src/modules/auth/auth.repository.ts
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { User, Session } from '@prisma/client';
import * as bcrypt from 'bcrypt';
import { v4 as uuidv4 } from 'uuid';

@Injectable()
export class AuthRepository {
  constructor(public prisma: PrismaService) {}

  async findUserByEmail(email: string): Promise<User | null> {
    return this.prisma.user.findUnique({
      where: { email },
      include: { role: true },
    });
  }

  async validatePassword(password: string, passwordHash: string): Promise<boolean> {
    return bcrypt.compare(password, passwordHash);
  }

  async createSession(userId: string, refreshToken: string, ip?: string, userAgent?: string, expiresInSec = 7 * 24 * 60 * 60) {
    const refreshTokenHash = await bcrypt.hash(refreshToken, 10);
    const expiresAt = new Date(Date.now() + expiresInSec * 1000);
    return this.prisma.session.create({
      data: {
        user: { connect: { id: userId } },
        refreshTokenHash,
        expiresAt,
        ipAddress: ip,
        userAgent,
      },
    });
  }

  async findSessionByTokenHash(hash: string) {
    return this.prisma.session.findFirst({ where: { refreshTokenHash: hash, isRevoked: false } });
  }

  async findSessionById(id: string): Promise<Session | null> {
    return this.prisma.session.findUnique({ where: { id } });
  }

  async revokeSession(sessionId: string) {
    return this.prisma.session.update({
      where: { id: sessionId },
      data: { isRevoked: true },
    });
  }
}
