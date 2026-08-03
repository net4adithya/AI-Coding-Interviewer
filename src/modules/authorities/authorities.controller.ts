// src/modules/authorities/authorities.controller.ts
import { Controller, Post, Get, Param, Body, UseGuards } from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiOperation, ApiResponse, ApiBody } from '@nestjs/swagger';
import { AuthoritiesService } from './authorities.service';
import { CreateAuthorityDto } from './dto/create-authority.dto';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { RolesGuard } from '../../common/guards/roles.guard';
import { Roles } from '../../common/decorators/roles.decorator';

@ApiTags('Authorities')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('AUTHORITY')
@Controller('authorities')
export class AuthoritiesController {
  constructor(private readonly authoritiesService: AuthoritiesService) {}

  @Post()
  @ApiOperation({ summary: 'Create Authority profile (Authority only)' })
  @ApiBody({ type: CreateAuthorityDto })
  @ApiResponse({ status: 201, description: 'Authority created' })
  async create(@Body() dto: CreateAuthorityDto) {
    return this.authoritiesService.create(dto);
  }

  @Get()
  @ApiOperation({ summary: 'List all Authority profiles' })
  @ApiResponse({ status: 200, description: 'Authorities retrieved' })
  async findAll() {
    return this.authoritiesService.findAll();
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get Authority by ID' })
  @ApiResponse({ status: 200, description: 'Authority retrieved' })
  async findById(@Param('id') id: string) {
    return this.authoritiesService.findById(id);
  }
}
