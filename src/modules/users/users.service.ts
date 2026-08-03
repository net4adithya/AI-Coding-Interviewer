// src/modules/users/users.service.ts
import { Injectable, ConflictException, NotFoundException } from '@nestjs/common';
import { UsersRepository } from './users.repository';
import { CreateUserDto } from './dto/create-user.dto';
import { UpdateUserDto } from './dto/update-user.dto';
import { UserResponseDto } from './dto/user-response.dto';
import { plainToClass } from 'class-transformer';

@Injectable()
export class UsersService {
  constructor(private readonly usersRepository: UsersRepository) {}

  async create(dto: CreateUserDto) {
    const existing = await this.usersRepository.findByEmail(dto.email);
    if (existing) {
      throw new ConflictException('Email already in use');
    }
    const user = await this.usersRepository.create(dto);
    return plainToClass(UserResponseDto, user, { excludeExtraneousValues: true });
  }

  async findAll() {
    const users = await this.usersRepository.findAll();
    return users.map((u) => plainToClass(UserResponseDto, u, { excludeExtraneousValues: true }));
  }

  async findOne(id: string) {
    const user = await this.usersRepository.findById(id);
    if (!user) {
      throw new NotFoundException(`User with id ${id} not found`);
    }
    return plainToClass(UserResponseDto, user, { excludeExtraneousValues: true });
  }

  async update(id: string, dto: UpdateUserDto) {
    const user = await this.usersRepository.findById(id);
    if (!user) {
      throw new NotFoundException(`User with id ${id} not found`);
    }
    const updated = await this.usersRepository.update(id, dto);
    return plainToClass(UserResponseDto, updated, { excludeExtraneousValues: true });
  }

  async remove(id: string) {
    const user = await this.usersRepository.findById(id);
    if (!user) {
      throw new NotFoundException(`User with id ${id} not found`);
    }
    await this.usersRepository.delete(id);
    return { message: 'User deleted successfully' };
  }
}
