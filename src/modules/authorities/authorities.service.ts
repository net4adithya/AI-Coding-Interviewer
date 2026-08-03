// src/modules/authorities/authorities.service.ts
import { Injectable, ConflictException, NotFoundException } from '@nestjs/common';
import { AuthoritiesRepository } from './authorities.repository';
import { CreateAuthorityDto } from './dto/create-authority.dto';
import { plainToClass } from 'class-transformer';

@Injectable()
export class AuthoritiesService {
  constructor(private readonly repo: AuthoritiesRepository) {}

  async create(dto: CreateAuthorityDto) {
    // Ensure the user exists and has AUTHORITY role – this could be validated elsewhere.
    const existing = await this.repo.prisma.authority.findUnique({ where: { userId: dto.userId } });
    if (existing) {
      throw new ConflictException('Authority profile already exists for this user');
    }
    const authority = await this.repo.create(dto);
    return authority;
  }

  async findAll() {
    return this.repo.findAll();
  }

  async findById(id: string) {
    const authority = await this.repo.findById(id);
    if (!authority) {
      throw new NotFoundException(`Authority with ID ${id} not found`);
    }
    return authority;
  }
}
