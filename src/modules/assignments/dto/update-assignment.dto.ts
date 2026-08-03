// src/modules/assignments/dto/update-assignment.dto.ts
import { PartialType } from '@nestjs/mapped-types';
import { CreateAssignmentDto } from './create-assignment.dto';
import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsOptional, IsEnum, IsUUID, IsDateString } from 'class-validator';
import { AssignmentDifficulty, AssignmentStatusEnum } from '@prisma/client';

export class UpdateAssignmentDto extends PartialType(CreateAssignmentDto) {
  @ApiPropertyOptional({ example: 'New Title' })
  @IsOptional()
  title?: string;

  @ApiPropertyOptional({ example: 'Updated description' })
  @IsOptional()
  description?: string;

  @ApiPropertyOptional({ enum: AssignmentDifficulty })
  @IsOptional()
  @IsEnum(AssignmentDifficulty)
  difficulty?: AssignmentDifficulty;

  @ApiPropertyOptional({ example: 'new-language-id-uuid' })
  @IsOptional()
  @IsUUID()
  languageId?: string;

  @ApiPropertyOptional({ example: '2026-10-01' })
  @IsOptional()
  @IsDateString()
  deadline?: string;

  @ApiPropertyOptional({ enum: AssignmentStatusEnum })
  @IsOptional()
  @IsEnum(AssignmentStatusEnum)
  status?: AssignmentStatusEnum;

  @ApiPropertyOptional({ example: 'new-intern-id-uuid' })
  @IsOptional()
  @IsUUID()
  internId?: string;
}
