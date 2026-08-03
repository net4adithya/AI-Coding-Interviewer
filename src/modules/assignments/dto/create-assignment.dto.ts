// src/modules/assignments/dto/create-assignment.dto.ts
import { ApiProperty } from '@nestjs/swagger';
import { IsString, IsNotEmpty, IsEnum, IsDateString, IsOptional, IsUUID } from 'class-validator';
import { AssignmentDifficulty, AssignmentStatusEnum } from '@prisma/client';

export class CreateAssignmentDto {
  @ApiProperty({ example: 'Build a NestJS Service' })
  @IsString()
  @IsNotEmpty()
  title: string;

  @ApiProperty({ example: 'Implement a service following clean architecture...' })
  @IsString()
  @IsNotEmpty()
  description: string;

  @ApiProperty({ enum: AssignmentDifficulty, example: AssignmentDifficulty.INTERMEDIATE })
  @IsEnum(AssignmentDifficulty)
  difficulty: AssignmentDifficulty;

  @ApiProperty({ example: 'language-id-uuid' })
  @IsUUID()
  languageId: string;

  @ApiProperty({ example: '2026-09-01' })
  @IsDateString()
  deadline: string;

  @ApiProperty({ enum: AssignmentStatusEnum, example: AssignmentStatusEnum.DRAFT })
  @IsEnum(AssignmentStatusEnum)
  @IsOptional()
  status?: AssignmentStatusEnum = AssignmentStatusEnum.DRAFT;

  @ApiProperty({ example: 'intern-id-uuid' })
  @IsOptional()
  @IsUUID()
  internId?: string;

  @ApiProperty({ example: 'authority-id-uuid' })
  @IsUUID()
  createdById: string; // Authority user ID
}
