// src/modules/assignments/assignments.controller.ts
import { Controller, Get, Post, Body, Param, Patch, Delete, Query, UseGuards } from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiCreatedResponse, ApiOkResponse, ApiNotFoundResponse, ApiForbiddenResponse, ApiBadRequestResponse } from '@nestjs/swagger';
import { AssignmentsService } from './assignments.service';
import { CreateAssignmentDto } from './dto/create-assignment.dto';
import { UpdateAssignmentDto } from './dto/update-assignment.dto';
import { QueryAssignmentsDto } from './dto/query-assignments.dto';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { RolesGuard } from '../../common/guards/roles.guard';
import { Roles } from '../../common/decorators/roles.decorator';
import { Role } from '@prisma/client';

@ApiTags('assignments')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard, RolesGuard)
@Controller('assignments')
export class AssignmentsController {
  constructor(private readonly assignmentsService: AssignmentsService) {}

  @Post()
  @Roles(Role.AUTHORITY)
  @ApiCreatedResponse({ description: 'Assignment created' })
  @ApiForbiddenResponse({ description: 'Only authorities can create assignments' })
  async create(@Body() dto: CreateAssignmentDto) {
    return this.assignmentsService.create(dto);
  }

  @Get()
  @Roles(Role.AUTHORITY, Role.INTERN)
  @ApiOkResponse({ description: 'List assignments with pagination, filters, sorting' })
  async findAll(@Query() query: QueryAssignmentsDto) {
    return this.assignmentsService.findAll(query);
  }

  @Get(':id')
  @Roles(Role.AUTHORITY, Role.INTERN)
  @ApiOkResponse({ description: 'Assignment details' })
  @ApiNotFoundResponse({ description: 'Assignment not found' })
  async findOne(@Param('id') id: string) {
    return this.assignmentsService.findOne(id);
  }

  @Patch(':id')
  @Roles(Role.AUTHORITY)
  @ApiOkResponse({ description: 'Assignment updated' })
  @ApiForbiddenResponse({ description: 'Only authorities can update assignments' })
  @ApiNotFoundResponse({ description: 'Assignment not found' })
  async update(@Param('id') id: string, @Body() dto: UpdateAssignmentDto) {
    return this.assignmentsService.update(id, dto);
  }

  @Delete(':id')
  @Roles(Role.AUTHORITY)
  @ApiOkResponse({ description: 'Assignment deleted' })
  @ApiForbiddenResponse({ description: 'Only authorities can delete assignments' })
  @ApiNotFoundResponse({ description: 'Assignment not found' })
  async remove(@Param('id') id: string) {
    return this.assignmentsService.delete(id);
  }
}
