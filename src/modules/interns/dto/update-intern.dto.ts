// src/modules/interns/dto/update-intern.dto.ts
import { PartialType } from '@nestjs/mapped-types';
import { CreateInternDto } from './create-intern.dto';
import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsOptional, IsUUID, IsString, IsDateString } from 'class-validator';

export class UpdateInternDto extends PartialType(CreateInternDto) {
  @ApiPropertyOptional({ description: 'Authority ID managing this intern', example: 'uuid-authority-id' })
  @IsOptional()
  @IsUUID()
  authorityId?: string;

  @ApiPropertyOptional({ description: 'Institution name', example: 'University of Example' })
  @IsOptional()
  @IsString()
  institution?: string;

  @ApiPropertyOptional({ description: 'Start date', example: '2023-01-01' })
  @IsOptional()
  @IsDateString()
  startDate?: string;

  @ApiPropertyOptional({ description: 'End date', example: '2023-12-31' })
  @IsOptional()
  @IsDateString()
  endDate?: string;
}
