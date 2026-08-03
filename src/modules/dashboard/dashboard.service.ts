// src/modules/dashboard/dashboard.service.ts
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { Role } from '@prisma/client';

@Injectable()
export class DashboardService {
  constructor(private prisma: PrismaService) {}

  // Authority view: total interns, active assignments, pending/completed reviews counts
  async getAuthorityDashboard(authorityId: string) {
    const [totalInterns, activeAssignments, pendingReviews, completedReviews] = await Promise.all([
      this.prisma.intern.count({ where: { authorityId } }),
      this.prisma.assignment.count({
        where: { authority: { id: authorityId }, status: { in: ['IN_PROGRESS', 'SUBMITTED'] } },
      }),
      this.prisma.assignment.count({
        where: { authority: { id: authorityId }, status: 'UNDER_REVIEW' },
      }),
      this.prisma.assignment.count({
        where: { authority: { id: authorityId }, status: 'COMPLETED' },
      }),
    ]);
    return { totalInterns, activeAssignments, pendingReviews, completedReviews };
  }

  // Intern view: assigned tasks, completed tasks, upcoming deadlines
  async getInternDashboard(internId: string) {
    const now = new Date();
    const [assignedTasks, completedTasks, upcomingDeadlines] = await Promise.all([
      this.prisma.assignment.count({ where: { internId } }),
      this.prisma.assignment.count({ where: { internId, status: 'COMPLETED' } }),
      this.prisma.assignment.count({
        where: { internId, deadline: { gte: now }, status: { in: ['DRAFT', 'IN_PROGRESS', 'PUBLISHED'] } },
      }),
    ]);
    return { assignedTasks, completedTasks, upcomingDeadlines };
  }
}
