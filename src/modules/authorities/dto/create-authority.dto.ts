// src/modules/authorities/dto/create-authority.dto.ts
import { ApiProperty } from '@nestjs/swagger';
import { IsString, IsNotEmpty } from 'class-validator';

export class CreateAuthorityDto {
  @ApiProperty({ example: 'Engineering' })
  @IsString()
  @IsNotEmpty()
  department: string;

  @ApiProperty({ example: 'Lead Software Architect' })
  @IsString()
  @IsNotEmpty()
  designation: string;

  @ApiProperty({ example: 'user-id-uuid' })
  @IsString()
  @IsNotEmpty()
  userId: string; // Must correspond to an existing User with AUTHORITY role
}
