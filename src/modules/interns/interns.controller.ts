// src/modules/interns/interns.controller.ts
import { Controller, Get, Post, Body, Param, Patch, Delete, UseGuards } from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiCreatedResponse, ApiOkResponse, ApiNotFoundResponse, ApiForbiddenResponse } from '@nestjs/swagger';
import { InternsService } from './interns.service';
import { CreateInternDto } from './dto/create-intern.dto';
import { UpdateInternDto } from './dto/update-intern.dto';
import { Roles } from '../../common/decorators/roles.decorator';
import { Role } from '@prisma/client';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { RolesGuard } from '../../common/guards/roles.guard';

@ApiTags('interns')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard, RolesGuard)
@Controller('interns')
export class InternsController {
  constructor(private readonly internsService: InternsService) {}

  @Post()
  @Roles(Role.AUTHORITY)
  @ApiCreatedResponse({ description: 'Intern created successfully' })
  @ApiForbiddenResponse({ description: 'Only authorities can create interns' })
  async create(@Body() dto: CreateInternDto) {
    // Role guard ensures only Authority reaches here
    return this.internsService.create(dto, Role.AUTHORITY);
  }

  @Get()
  @Roles(Role.AUTHORITY)
  @ApiOkResponse({ description: 'List of interns' })
  async findAll() {
    return this.internsService.findAll();
  }

  @Get(':id')
  @Roles(Role.AUTHORITY, Role.INTERN)
  @ApiOkResponse({ description: 'Intern details' })
  @ApiNotFoundResponse({ description: 'Intern not found' })
  async findOne(@Param('id') id: string) {
    return this.internsService.findOne(id);
  }

  @Patch(':id')
  @Roles(Role.AUTHORITY)
  @ApiOkResponse({ description: 'Intern updated' })
  @ApiForbiddenResponse({ description: 'Only authorities can update interns' })
  async update(@Param('id') id: string, @Body() dto: UpdateInternDto) {
    return this.internsService.update(id, dto, Role.AUTHORITY);
  }

  @Delete(':id')
  @Roles(Role.AUTHORITY)
  @ApiOkResponse({ description: 'Intern deleted' })
  @ApiForbiddenResponse({ description: 'Only authorities can delete interns' })
  async remove(@Param('id') id: string) {
    return this.internsService.remove(id, Role.AUTHORITY);
  }
}
