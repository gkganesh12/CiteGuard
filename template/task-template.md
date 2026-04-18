# Task Template

Use this template for individual development tasks. Tasks are typically part of a larger feature and represent actionable work items.

---

## Task Information

### Task Title

<!-- e.g., Implement User Login API Endpoint, Create Booking Form Component -->

### Task ID

<!-- e.g., TASK-001 or FEAT-002-BE-01 -->

### Related Feature

<!-- e.g., FEAT-002: Authentication System -->
<!-- Link: [FEAT-002](../board/Features/BE/FEAT-002-authentication-login-system.md) -->

### Type

<!-- Options: Frontend | Backend | Database | DevOps | Documentation | Testing | Bug Fix -->

### Status

<!-- Options: To Do | In Progress | Blocked | In Review | Testing | Done -->

### Assigned To

<!-- Developer name -->

### Priority

<!-- Options: Critical | High | Medium | Low -->

### Estimated Hours

<!-- e.g., 4 hours -->

### Actual Hours

<!-- Fill in when completed: e.g., 5 hours -->

### Start Date

<!-- e.g., 2024-01-15 -->

### Completion Date

<!-- e.g., 2024-01-16 -->

---

## Task Description

### Summary

<!-- Brief description of what needs to be done -->

### Background

<!-- Context: Why is this task needed? What's the bigger picture? -->

### Dependencies

<!-- List any tasks that must be completed before this one -->

- [ ] Dependency 1 (e.g., TASK-XXX: Database schema migration)
- [ ] Dependency 2 (e.g., API contract agreed with frontend team)

### Blockers

<!-- Any current blockers preventing progress? -->

- [ ] Blocker 1 (if any)
- [ ] Blocker 2 (if any)

---

## Technical Details

### Technology Stack

<!-- e.g., NestJS, React, PostgreSQL, etc. -->

### Files to be Modified/Created

<!-- List the files that will be affected -->

**New Files:**
```
- src/modules/auth/auth.controller.ts
- src/modules/auth/auth.service.ts
- src/modules/auth/dto/login.dto.ts
```

**Modified Files:**
```
- src/app.module.ts
- README.md
```

### API Endpoints (if applicable)

**Endpoint:** `POST /api/v1/auth/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "accessToken": "jwt-token-here",
  "refreshToken": "refresh-token-here",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "USER"
  }
}
```

### Database Changes (if applicable)

**Tables Affected:**
- Table: `users`
- Table: `sessions`

**Migration Required:** Yes / No

**Migration File:** `20240115_add_sessions_table.sql`

---

## Implementation Plan

### Step-by-Step Approach

- [ ] Step 1: Setup module structure (controller, service, DTOs)
- [ ] Step 2: Implement validation with class-validator
- [ ] Step 3: Implement business logic in service layer
- [ ] Step 4: Add authentication guards
- [ ] Step 5: Write unit tests for service
- [ ] Step 6: Write integration tests for API endpoint
- [ ] Step 7: Add Swagger documentation
- [ ] Step 8: Manual testing with Postman
- [ ] Step 9: Code review and address feedback
- [ ] Step 10: Update documentation

### Key Components

**For Backend Tasks:**
- [ ] Repository layer (database operations)
- [ ] Service layer (business logic)
- [ ] Controller layer (API endpoints)
- [ ] DTOs (request/response validation)
- [ ] Guards/Pipes/Interceptors (if needed)
- [ ] Error handling
- [ ] Logging

**For Frontend Tasks:**
- [ ] Component structure
- [ ] State management (Redux/Context)
- [ ] API integration
- [ ] Form validation
- [ ] Error handling
- [ ] Loading states
- [ ] Responsive design
- [ ] Accessibility (a11y)

---

## Acceptance Criteria

<!-- Define clear criteria for when this task is considered complete -->

- [ ] Functional requirement 1 implemented and working
- [ ] Functional requirement 2 implemented and working
- [ ] All edge cases handled
- [ ] Error handling implemented
- [ ] Unit tests written and passing (coverage > 80%)
- [ ] Integration tests written and passing
- [ ] Code follows project coding standards
- [ ] No console.log or commented code
- [ ] Documentation updated
- [ ] Code reviewed and approved
- [ ] Tested manually in development environment
- [ ] No linting errors
- [ ] No security vulnerabilities

---

## Testing Strategy

### Unit Tests

**Files:**
```
- auth.service.spec.ts
- auth.controller.spec.ts
```

**Test Cases:**
- [ ] Test successful login
- [ ] Test login with invalid credentials
- [ ] Test login with missing fields
- [ ] Test JWT token generation
- [ ] Test password hashing verification

### Integration Tests

**Test Scenarios:**
- [ ] End-to-end login flow
- [ ] Error responses for various scenarios
- [ ] Authentication guard functionality

### Manual Testing Checklist

- [ ] Happy path: Successful login
- [ ] Invalid email format
- [ ] Invalid password
- [ ] Non-existent user
- [ ] Account locked scenario
- [ ] Network error handling
- [ ] Browser console: No errors
- [ ] Responsive design: Mobile, tablet, desktop

---

## Code Quality Checklist

### Before Creating PR

- [ ] Code follows SOLID principles
- [ ] No code duplication
- [ ] Functions are small and focused (<30 lines)
- [ ] Proper error handling implemented
- [ ] All inputs validated
- [ ] Security best practices followed
- [ ] Performance optimized
- [ ] TypeScript types properly defined (no `any`)
- [ ] Comments explain complex logic
- [ ] JSDoc added for public methods
- [ ] All tests passing
- [ ] Linting passes with no errors
- [ ] No hard-coded values (use constants/env vars)

### Backend Specific

- [ ] Repository pattern used (no direct Prisma in services)
- [ ] DTOs for all inputs/outputs
- [ ] Proper HTTP status codes
- [ ] Swagger decorators added
- [ ] Database queries optimized
- [ ] Transactions used where needed
- [ ] Authentication/authorization implemented
- [ ] Logging added for important operations

### Frontend Specific

- [ ] Component is reusable and follows SRP
- [ ] Props properly typed
- [ ] Hooks used correctly
- [ ] Memoization used where needed (useMemo, useCallback)
- [ ] Accessibility standards met (WCAG 2.1 AA)
- [ ] Responsive design implemented
- [ ] Loading and error states handled
- [ ] User feedback provided for all actions

---

## Documentation

### Code Comments

<!-- Have you added comments for complex logic? -->

- [ ] Complex algorithms explained
- [ ] Business logic rationale documented
- [ ] JSDoc for public methods

### API Documentation

<!-- For backend tasks -->

- [ ] Swagger/OpenAPI decorators added
- [ ] Request/response examples provided
- [ ] Error responses documented

### README Updates

<!-- If changes affect setup or usage -->

- [ ] Installation instructions updated
- [ ] Environment variables documented
- [ ] Usage examples added

---

## Review & Collaboration

### Frontend-Backend Coordination

<!-- If this task requires coordination with other team -->

**API Contract:**
- [ ] Endpoint structure agreed
- [ ] Request/response format confirmed
- [ ] Error handling approach aligned
- [ ] Authentication mechanism confirmed

**Dependencies:**
- [ ] Backend API ready for frontend integration
- [ ] Mock data provided for parallel development

### Code Review Checklist

**Reviewer:**
- [ ] Code follows project guidelines (FE_dev.md / BE_dev.md)
- [ ] SOLID principles adhered to
- [ ] No code duplication
- [ ] Tests are comprehensive
- [ ] Security considerations addressed
- [ ] Performance is acceptable
- [ ] Documentation is clear
- [ ] PR description is complete

---

## Deployment

### Pre-Deployment Checklist

- [ ] All tests passing in CI/CD
- [ ] Code merged to main branch
- [ ] Database migrations reviewed and ready
- [ ] Environment variables configured
- [ ] Staging deployment successful
- [ ] Staging testing completed

### Post-Deployment

- [ ] Production deployment successful
- [ ] Smoke tests passed
- [ ] Monitoring dashboards checked
- [ ] No errors in logs
- [ ] Feature flag enabled (if applicable)

---

## Notes & Learnings

### Technical Decisions

<!-- Document any important technical decisions made during implementation -->

**Decision 1:**
- **Context:** 
- **Decision:** 
- **Rationale:** 

### Challenges Faced

<!-- What challenges did you encounter and how did you solve them? -->

1. Challenge 1
   - **Issue:** 
   - **Solution:** 

### Learnings

<!-- What did you learn from this task? -->

- Learning 1
- Learning 2

### Future Improvements

<!-- What could be improved in the future? -->

- Improvement 1
- Improvement 2

---

## Links & Resources

### Related Documents

- Feature Document: [FEAT-XXX](link-to-feature)
- ADR: [ADR-XXX](link-to-adr)
- Design Mockups: [Figma Link](link-to-figma)

### API Documentation

- Swagger UI: `http://localhost:3000/api/docs`
- Postman Collection: [Link](link-to-postman)

### Helpful Resources

- Library Documentation: [Link](url)
- Stack Overflow Discussion: [Link](url)
- Tutorial/Article: [Link](url)

---

## Status Updates

### Update 1 - [Date]

**Progress:**
- Completed: 
- In Progress: 
- Blocked: 

**Notes:**


### Update 2 - [Date]

**Progress:**
- Completed: 
- In Progress: 
- Blocked: 

**Notes:**


---

## Completion Checklist

### Final Review

- [ ] All acceptance criteria met
- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] Deployed to staging
- [ ] Tested in staging
- [ ] Deployed to production
- [ ] Verified in production
- [ ] Status updated to Done
- [ ] Stakeholders notified

### Sign-Off

**Developer:** <!-- Name -->
**Date Completed:** <!-- Date -->
**Reviewer:** <!-- Name -->
**Date Reviewed:** <!-- Date -->

---

## Template Usage Instructions

1. **Copy this template** to create a new task
2. **Name the file** using convention: `TASK-XXX-brief-description.md` or `FEAT-XXX-TYPE-NN.md`
3. **Fill in all sections** that are relevant to your task
4. **Remove sections** that don't apply (e.g., API endpoints for non-API tasks)
5. **Update status regularly** as you progress through the task
6. **Check off items** as you complete them
7. **Document learnings** at the end for future reference
8. **Keep it updated** - this is your working document

---

**Remember:** A good task document makes collaboration easier, prevents miscommunication, and serves as documentation for future reference. Take time to fill it out properly! 🚀
