import { Injectable, ConflictException, NotFoundException } from '@nestjs/common';
import { RolesRepository } from './roles.repository';
import { CreateRoleDto } from './dto/create-role.dto';

@Injectable()
export class RolesService {
  constructor(private readonly rolesRepository: RolesRepository) {}

  async create(dto: CreateRoleDto) {
    const existing = await this.rolesRepository.findByName(dto.name);
    if (existing) {
      throw new ConflictException(`Role '${dto.name}' already exists`);
    }
    return this.rolesRepository.create(dto);
  }

  async findAll() {
    return this.rolesRepository.findAll();
  }

  async findById(id: string) {
    const role = await this.rolesRepository.findById(id);
    if (!role) {
      throw new NotFoundException(`Role with ID '${id}' not found`);
    }
    return role;
  }

  async findByName(name: string) {
    const role = await this.rolesRepository.findByName(name);
    if (!role) {
      throw new NotFoundException(`Role '${name}' not found`);
    }
    return role;
  }
}
