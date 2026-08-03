// src/modules/assignments/dto/query-assignments.dto.ts
import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsOptional, IsNumberString, IsEnum, IsUUID, IsString } from 'class-validator';
import { AssignmentDifficulty, AssignmentStatusEnum } from '@prisma/client';

export class QueryAssignmentsDto {
  @ApiPropertyOptional({ description: 'Page number', example: 1 })
  @IsOptional()
  @IsNumberString()
  page?: string;

  @ApiPropertyOptional({ description: 'Items per page', example: 10 })
  @IsOptional()
  @IsNumberString()
  limit?: string;

  @ApiPropertyOptional({ description: 'Field to sort by', example: 'createdAt' })
  @IsOptional()
  @IsString()
  sortBy?: string;

  @ApiPropertyOptional({ description: 'Sort order (asc or desc)', example: 'desc' })
  @IsOptional()
  @IsString()
  sortOrder?: string;

  @ApiPropertyOptional({ description: 'Search term for title/description' })
  @IsOptional()
  @IsString()
  search?: string;

  @ApiPropertyOptional({ enum: AssignmentStatusEnum, description: 'Filter by status' })
  @IsOptional()
  @IsEnum(AssignmentStatusEnum)
  status?: AssignmentStatusEnum;

  @ApiPropertyOptional({ enum: AssignmentDifficulty, description: 'Filter by difficulty' })
  @IsOptional()
  @IsEnum(AssignmentDifficulty)
  difficulty?: AssignmentDifficulty;

  @ApiPropertyOptional({ description: 'Filter by programming language ID', example: 'uuid-language-id' })
  @IsOptional()
  @IsUUID()
  languageId?: string;
}
