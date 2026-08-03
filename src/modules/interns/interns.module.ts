// src/modules/interns/interns.module.ts
import { Module } from '@nestjs/common';
import { InternsService } from './interns.service';
import { InternsController } from './interns.controller';
import { InternsRepository } from './interns.repository';
import { PrismaModule } from '../../prisma/prisma.module';

@Module({
  imports: [PrismaModule],
  controllers: [InternsController],
  providers: [InternsService, InternsRepository],
  exports: [InternsService],
})
export class InternsModule {}
