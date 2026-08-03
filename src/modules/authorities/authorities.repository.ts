// src/modules/authorities/authorities.repository.ts
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { CreateAuthorityDto } from './dto/create-authority.dto';

@Injectable()
export class AuthoritiesRepository {
  constructor(private prisma: PrismaService) {}

  async create(dto: CreateAuthorityDto) {
    return this.prisma.authority.create({
      data: {
        department: dto.department,
        designation: dto.designation,
        user: { connect: { id: dto.userId } },
      },
    });
  }

  async findAll() {
    return this.prisma.authority.findMany({
      include: { user: true },
    });
  }

  async findById(id: string) {
    return this.prisma.authority.findUnique({
      where: { id },
      include: { user: true },
    });
  }
}
