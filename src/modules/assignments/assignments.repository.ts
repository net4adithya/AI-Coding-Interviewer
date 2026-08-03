// src/modules/assignments/assignments.repository.ts
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { CreateAssignmentDto } from './dto/create-assignment.dto';
import { UpdateAssignmentDto } from './dto/update-assignment.dto';
import { AssignmentDifficulty, AssignmentStatusEnum } from '@prisma/client';

@Injectable()
export class AssignmentsRepository {
  constructor(private prisma: PrismaService) {}

  async create(dto: CreateAssignmentDto) {
    return this.prisma.assignment.create({
      data: {
        title: dto.title,
        description: dto.description,
        difficulty: dto.difficulty,
        language: { connect: { id: dto.languageId } },
        deadline: new Date(dto.deadline),
        status: dto.status ?? AssignmentStatusEnum.DRAFT,
        intern: dto.internId ? { connect: { id: dto.internId } } : undefined,
        createdBy: { connect: { id: dto.createdById } },
      },
    });
  }

  async update(id: string, dto: UpdateAssignmentDto) {
    const data: any = { ...dto };
    if (dto.deadline) data.deadline = new Date(dto.deadline);
    if (dto.languageId) data.language = { connect: { id: dto.languageId } };
    if (dto.internId) data.intern = { connect: { id: dto.internId } };
    if (dto.status) data.status = dto.status;
    return this.prisma.assignment.update({ where: { id }, data });
  }

  async delete(id: string) {
    return this.prisma.assignment.delete({ where: { id } });
  }

  async findById(id: string) {
    return this.prisma.assignment.findUnique({
      where: { id },
      include: { language: true, createdBy: true, intern: true },
    });
  }

  async findAll(params: any) {
    const { page = 1, limit = 10, sortBy = 'createdAt', sortOrder = 'desc', search, status, difficulty, languageId } = params;
    const skip = (page - 1) * limit;
    const where: any = {};
    if (search) {
      where.OR = [
        { title: { contains: search, mode: 'insensitive' } },
        { description: { contains: search, mode: 'insensitive' } },
      ];
    }
    if (status) where.status = status;
    if (difficulty) where.difficulty = difficulty;
    if (languageId) where.languageId = languageId;

    const [total, items] = await Promise.all([
      this.prisma.assignment.count({ where }),
      this.prisma.assignment.findMany({
        where,
        skip,
        take: limit,
        orderBy: { [sortBy]: sortOrder },
        include: { language: true, createdBy: true, intern: true },
      }),
    ]);
    return { total, items, page, limit };
  }
}
