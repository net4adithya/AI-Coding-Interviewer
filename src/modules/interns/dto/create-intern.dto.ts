// src/modules/interns/dto/create-intern.dto.ts
import { ApiProperty } from '@nestjs/swagger';
import { IsUUID, IsOptional, IsString, IsDateString } from 'class-validator';

export class CreateInternDto {
  @ApiProperty({ description: 'User ID linked to the intern profile', example: 'uuid-user-id' })
  @IsUUID()
  userId: string;

  @ApiProperty({ description: 'Authority ID managing this intern (optional)', example: 'uuid-authority-id', required: false })
  @IsOptional()
  @IsUUID()
  authorityId?: string;

  @ApiProperty({ description: 'Name of the educational institution', example: 'University of Example', required: false })
  @IsOptional()
  @IsString()
  institution?: string;

  @ApiProperty({ description: 'Internship start date (ISO string)', example: '2023-01-01', required: false })
  @IsOptional()
  @IsDateString()
  startDate?: string;

  @ApiProperty({ description: 'Internship end date (ISO string)', example: '2023-12-31', required: false })
  @IsOptional()
  @IsDateString()
  endDate?: string;
}
