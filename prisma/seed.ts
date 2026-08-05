import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Starting Database Seeding...');

  // 1. Seed Roles
  const authorityRole = await prisma.role.upsert({
    where: { name: 'AUTHORITY' },
    update: {},
    create: {
      name: 'AUTHORITY',
      description: 'Manager / Team Lead with administrative & review access',
      permissions: JSON.stringify([
        'users:read',
        'interns:manage',
        'assignments:create',
        'assignments:read',
        'assignments:update',
        'assignments:delete',
        'dashboard:authority',
        'audit:read',
      ]),
    },
  });

  const internRole = await prisma.role.upsert({
    where: { name: 'INTERN' },
    update: {},
    create: {
      name: 'INTERN',
      description: 'Intern completing assigned coding challenges',
      permissions: JSON.stringify([
        'assignments:read',
        'dashboard:intern',
        'profile:read',
      ]),
    },
  });

  console.log('✅ Roles seeded: AUTHORITY, INTERN');

  // 2. Seed Programming Languages
  const languages = [
    { name: 'TypeScript', slug: 'typescript' },
    { name: 'JavaScript', slug: 'javascript' },
    { name: 'Python', slug: 'python' },
    { name: 'Java', slug: 'java' },
    { name: 'C++', slug: 'cpp' },
  ];

  for (const lang of languages) {
    await prisma.programmingLanguage.upsert({
      where: { slug: lang.slug },
      update: {},
      create: lang,
    });
  }

  console.log('✅ Programming Languages seeded');

  // 3. Seed Assignment Statuses
  const statuses = [
    { name: 'Draft', code: 'DRAFT', description: 'Assignment is in draft mode' },
    { name: 'Published', code: 'PUBLISHED', description: 'Assignment is published for interns' },
    { name: 'In Progress', code: 'IN_PROGRESS', description: 'Intern is working on the assignment' },
    { name: 'Submitted', code: 'SUBMITTED', description: 'Assignment submitted by intern' },
    { name: 'Under Review', code: 'UNDER_REVIEW', description: 'Assignment under review by AI/Authority' },
    { name: 'Completed', code: 'COMPLETED', description: 'Assignment completed' },
    { name: 'Archived', code: 'ARCHIVED', description: 'Assignment archived' },
  ];

  for (const st of statuses) {
    await prisma.assignmentStatus.upsert({
      where: { code: st.code },
      update: {},
      create: st,
    });
  }

  console.log('✅ Assignment Statuses seeded');

  // 4. Seed Seed Users & Profiles
  const defaultPasswordHash = await bcrypt.hash('Password123!', 10);

  // Authority User
  const authorityUser = await prisma.user.upsert({
    where: { email: 'authority@platform.com' },
    update: { passwordHash: defaultPasswordHash },
    create: {
      email: 'authority@platform.com',
      passwordHash: defaultPasswordHash,
      firstName: 'Sarah',
      lastName: 'Connor',
      roleId: authorityRole.id,
      authority: {
        create: {
          department: 'Engineering',
          designation: 'Lead Software Architect',
        },
      },
    },
    include: { authority: true },
  });

  // Intern User
  const internUser = await prisma.user.upsert({
    where: { email: 'intern@platform.com' },
    update: { passwordHash: defaultPasswordHash },
    create: {
      email: 'intern@platform.com',
      passwordHash: defaultPasswordHash,
      firstName: 'Alex',
      lastName: 'Mercer',
      roleId: internRole.id,
      intern: {
        create: {
          authorityId: authorityUser.authority?.id,
          institution: 'Tech University',
          startDate: new Date('2026-06-01'),
          endDate: new Date('2026-12-31'),
        },
      },
    },
    include: { intern: true },
  });

  console.log('✅ Default users seeded: authority@platform.com, intern@platform.com (Password: Password123!)');

  // 5. Seed Sample Assignment
  const tsLang = await prisma.programmingLanguage.findUnique({ where: { slug: 'typescript' } });

  if (tsLang && internUser.intern) {
    await prisma.assignment.create({
      data: {
        title: 'Implement Clean Architecture Microservice In NestJS',
        description: 'Build a modular NestJS service with JWT Authentication, Prisma ORM, and RBAC Guards.',
        difficulty: 'INTERMEDIATE',
        languageId: tsLang.id,
        deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days from now
        status: 'PUBLISHED',
        createdById: authorityUser.id,
        internId: internUser.intern.id,
      },
    });
    console.log('✅ Sample assignment created');
  }

  console.log('🎉 Seeding Completed Successfully!');
}

main()
  .catch((e) => {
    console.error('❌ Seeding failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
