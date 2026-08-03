// src/modules/auth/auth.service.ts
import { Injectable, UnauthorizedException, BadRequestException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { AuthRepository } from './auth.repository';
import { LoginDto } from './dto/login.dto';
import { RefreshTokenDto } from './dto/refresh-token.dto';
import { JwtPayload, AuthenticatedUser } from '../../common/interfaces/authenticated-user.interface';
import { v4 as uuidv4 } from 'uuid';
import * as bcrypt from 'bcrypt';

@Injectable()
export class AuthService {
  constructor(
    private readonly authRepository: AuthRepository,
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
  ) {}

  private async _generateJwtPayload(user: any): Promise<JwtPayload> {
    const role = user.role?.name || user.role;
    const permissions = user.role?.permissions || [];
    return {
      sub: user.id,
      email: user.email,
      role,
      permissions,
    };
  }

  async login(dto: LoginDto) {
    const user = await this.authRepository.findUserByEmail(dto.email);
    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }
    const passwordValid = await this.authRepository.validatePassword(
      dto.password,
      user.passwordHash,
    );
    if (!passwordValid) {
      throw new UnauthorizedException('Invalid credentials');
    }

    const payload = await this._generateJwtPayload(user);
    const accessToken = this.jwtService.sign(payload, {
      secret: this.configService.get<string>('jwt.secret'),
      expiresIn: this.configService.get<string>('jwt.expiresIn'),
    });

    // create a session and embed the sessionId into refresh token payload
    const sessionId = uuidv4();
    const refreshPayload = { sub: user.id, sessionId };
    const refreshToken = this.jwtService.sign(refreshPayload, {
      secret: this.configService.get<string>('jwt.refreshSecret'),
      expiresIn: this.configService.get<string>('jwt.refreshExpiresIn'),
    });

    await this.authRepository.createSession(
      user.id,
      refreshToken,
      undefined,
      undefined,
    );

    return {
      accessToken,
      refreshToken,
      user: {
        id: user.id,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        role: payload.role,
        permissions: payload.permissions,
      },
    };
  }

  async refresh(dto: RefreshTokenDto) {
    try {
      const decoded = this.jwtService.verify(dto.refreshToken, {
        secret: this.configService.get<string>('jwt.refreshSecret'),
      }) as any;
      const sessionId = decoded.sessionId;
      if (!sessionId) {
        throw new BadRequestException('Invalid refresh token payload');
      }
      const session = await this.authRepository.prisma.session.findUnique({
        where: { id: sessionId },
      });
      if (!session || session.isRevoked) {
        throw new UnauthorizedException('Refresh token revoked');
      }
      // Issue new tokens
      const user = await this.authRepository.prisma.user.findUnique({
        where: { id: decoded.sub },
        include: { role: true },
      });
      if (!user) {
        throw new UnauthorizedException('User not found');
      }
      const payload = await this._generateJwtPayload(user);
      const accessToken = this.jwtService.sign(payload, {
        secret: this.configService.get<string>('jwt.secret'),
        expiresIn: this.configService.get<string>('jwt.expiresIn'),
      });

      // rotate refresh token
      const newSessionId = uuidv4();
      const newRefreshPayload = { sub: user.id, sessionId: newSessionId };
      const newRefreshToken = this.jwtService.sign(newRefreshPayload, {
        secret: this.configService.get<string>('jwt.refreshSecret'),
        expiresIn: this.configService.get<string>('jwt.refreshExpiresIn'),
      });
      await this.authRepository.createSession(user.id, newRefreshToken);

      // revoke old session
      await this.authRepository.revokeSession(sessionId);

      return { accessToken, refreshToken: newRefreshToken };
    } catch (err) {
      throw new UnauthorizedException('Invalid refresh token');
    }
  }

  async logout(dto: RefreshTokenDto) {
    // Similar to refresh: identify session and revoke it
    try {
      const decoded = this.jwtService.verify(dto.refreshToken, {
        secret: this.configService.get<string>('jwt.refreshSecret'),
      }) as any;
      const sessionId = decoded.sessionId;
      if (!sessionId) {
        throw new BadRequestException('Invalid token');
      }
      await this.authRepository.revokeSession(sessionId);
      return { message: 'Logged out successfully' };
    } catch (err) {
      throw new UnauthorizedException('Invalid token');
    }
  }

  async me(user: AuthenticatedUser) {
    return user;
  }
}
