// src/modules/assignments/assignments.service.ts
import { Injectable, NotFoundException } from '@nestjs/common';
import { AssignmentsRepository } from './assignments.repository';
import { CreateAssignmentDto } from './dto/create-assignment.dto';
import { UpdateAssignmentDto } from './dto/update-assignment.dto';

@Injectable()
export class AssignmentsService {
  constructor(private readonly repo: AssignmentsRepository) {}

  async create(dto: CreateAssignmentDto) {
    return this.repo.create(dto);
  }

  async update(id: string, dto: UpdateAssignmentDto) {
    const existing = await this.repo.findById(id);
    if (!existing) {
      throw new NotFoundException(`Assignment with id ${id} not found`);
    }
    return this.repo.update(id, dto);
  }

  async delete(id: string) {
    const existing = await this.repo.findById(id);
    if (!existing) {
      throw new NotFoundException(`Assignment with id ${id} not found`);
    }
    return this.repo.delete(id);
  }

  async findOne(id: string) {
    const assignment = await this.repo.findById(id);
    if (!assignment) {
      throw new NotFoundException(`Assignment with id ${id} not found`);
    }
    return assignment;
  }

  async findAll(params: any) {
    // params includes pagination, filters, sorting (from query DTO)
    return this.repo.findAll(params);
  }
}
