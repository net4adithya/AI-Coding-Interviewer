import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsString, IsNotEmpty, IsOptional, IsArray } from 'class-validator';

export class CreateRoleDto {
  @ApiProperty({ example: 'AUTHORITY' })
  @IsString()
  @IsNotEmpty()
  name: string;

  @ApiPropertyOptional({ example: 'Manager or Team Lead role' })
  @IsOptional()
  @IsString()
  description?: string;

  @ApiProperty({ example: ['assignments:create', 'interns:manage'] })
  @IsArray()
  @IsString({ each: true })
  permissions: string[];
}
