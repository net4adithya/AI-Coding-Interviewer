// src/modules/interns/interns.service.ts
import { Injectable, NotFoundException, ForbiddenException } from '@nestjs/common';
import { InternsRepository } from './interns.repository';
import { CreateInternDto } from './dto/create-intern.dto';
import { UpdateInternDto } from './dto/update-intern.dto';
import { Roles } from '../../common/decorators/roles.decorator';
import { Role } from '@prisma/client';

@Injectable()
export class InternsService {
  constructor(private readonly repo: InternsRepository) {}

  async create(dto: CreateInternDto, currentUserRole: Role) {
    if (currentUserRole !== Role.AUTHORITY) {
      throw new ForbiddenException('Only authorities can create interns');
    }
    return this.repo.create(dto);
  }

  async findAll() {
    return this.repo.findAll();
  }

  async findOne(id: string) {
    const intern = await this.repo.findById(id);
    if (!intern) {
      throw new NotFoundException(`Intern with id ${id} not found`);
    }
    return intern;
  }

  async update(id: string, dto: UpdateInternDto, currentUserRole: Role) {
    if (currentUserRole !== Role.AUTHORITY) {
      throw new ForbiddenException('Only authorities can update interns');
    }
    const existing = await this.repo.findById(id);
    if (!existing) {
      throw new NotFoundException(`Intern with id ${id} not found`);
    }
    // Simple merge logic – Prisma update will handle optional fields
    return this.repo.prisma.intern.update({
      where: { id },
      data: {
        authorityId: dto.authorityId ?? existing.authorityId,
        institution: dto.institution ?? existing.institution,
        startDate: dto.startDate ? new Date(dto.startDate) : existing.startDate,
        endDate: dto.endDate ? new Date(dto.endDate) : existing.endDate,
      },
    });
  }

  async remove(id: string, currentUserRole: Role) {
    if (currentUserRole !== Role.AUTHORITY) {
      throw new ForbiddenException('Only authorities can delete interns');
    }
    const existing = await this.repo.findById(id);
    if (!existing) {
      throw new NotFoundException(`Intern with id ${id} not found`);
    }
    return this.repo.prisma.intern.delete({ where: { id } });
  }
}
