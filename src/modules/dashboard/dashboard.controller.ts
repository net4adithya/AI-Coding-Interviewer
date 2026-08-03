// src/modules/dashboard/dashboard.controller.ts
import { Controller, Get, Param, UseGuards, Req } from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiOkResponse, ApiForbiddenResponse } from '@nestjs/swagger';
import { DashboardService } from './dashboard.service';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { RolesGuard } from '../../common/guards/roles.guard';
import { Roles } from '../../common/decorators/roles.decorator';
import { Role } from '@prisma/client';
import { Request } from 'express';

@ApiTags('dashboard')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard, RolesGuard)
@Controller('dashboard')
export class DashboardController {
  constructor(private readonly dashboardService: DashboardService) {}

  @Get('authority/:authorityId')
  @Roles(Role.AUTHORITY)
  @ApiOkResponse({ description: 'Authority dashboard data' })
  @ApiForbiddenResponse({ description: 'Only authorities can access this endpoint' })
  async getAuthorityDashboard(@Param('authorityId') authorityId: string) {
    return this.dashboardService.getAuthorityDashboard(authorityId);
  }

  @Get('intern/:internId')
  @Roles(Role.INTERN)
  @ApiOkResponse({ description: 'Intern dashboard data' })
  @ApiForbiddenResponse({ description: 'Only interns can access this endpoint' })
  async getInternDashboard(@Param('internId') internId: string) {
    return this.dashboardService.getInternDashboard(internId);
  }
}
