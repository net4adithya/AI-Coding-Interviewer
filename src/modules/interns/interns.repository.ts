// src/modules/interns/interns.repository.ts
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { CreateInternDto } from './dto/create-intern.dto';
import { UpdateInternDto } from './dto/update-intern.dto';

@Injectable()
export class InternsRepository {
  constructor(public prisma: PrismaService) {}

  async create(dto: CreateInternDto) {
    return this.prisma.intern.create({
      data: {
        user: { connect: { id: dto.userId } },
        authority: dto.authorityId ? { connect: { id: dto.authorityId } } : undefined,
        institution: dto.institution,
        startDate: dto.startDate ? new Date(dto.startDate) : undefined,
        endDate: dto.endDate ? new Date(dto.endDate) : undefined,
      },
    });
  }

  async findAll() {
    return this.prisma.intern.findMany({
      include: { user: true, authority: true, assignments: true },
    });
  }

  async findById(id: string) {
    return this.prisma.intern.findUnique({
      where: { id },
      include: { user: true, authority: true, assignments: true },
    });
  }

  async update(id: string, dto: UpdateInternDto) {
    const data: any = {};
    if (dto.authorityId !== undefined) data.authority = { connect: { id: dto.authorityId } };
    if (dto.institution !== undefined) data.institution = dto.institution;
    if (dto.startDate !== undefined) data.startDate = new Date(dto.startDate);
    if (dto.endDate !== undefined) data.endDate = new Date(dto.endDate);
    return this.prisma.intern.update({ where: { id }, data });
  }

  async delete(id: string) {
    return this.prisma.intern.delete({ where: { id } });
  }
}
