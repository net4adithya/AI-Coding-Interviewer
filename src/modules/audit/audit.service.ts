import { Injectable } from '@nestjs/common';
import { AuditRepository } from './audit.repository';
import { CreateAuditLogDto } from './dto/create-audit-log.dto';
import { PaginationDto } from '../../common/dto/pagination.dto';

@Injectable()
export class AuditService {
  constructor(private readonly auditRepository: AuditRepository) {}

  async log(data: CreateAuditLogDto) {
    return this.auditRepository.create(data);
  }

  async findAll(pagination: PaginationDto) {
    return this.auditRepository.findAll(pagination);
  }
}
