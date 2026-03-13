# Quiz

## Section 1

### 1.1 Salary Calculation

- Let x = old salary
- newSalary = x + 0.12x = 1.12x
- 575 = 1.12x
- 575/1.12 = x
- **Old Salary = 513.39**

---

### 1.2 Age Ordering Problem

**Given:** Kevin (K), Nicholas (N), Joseph (J)

**Conditions:**

- Kevin is oldest
- N is not oldest → N can be middle or youngest
- J is not youngest → J is middle (cannot be oldest or youngest)

**Result:** From the requirements above, N is youngest

**Final Order:** Kevin (oldest) → Joseph (middle) → Nicholas (youngest)

---

### 1.3 Triangle Count

**Result:** 12 triangles in the picture

---

### 1.4 System of Equations

```
A + B = 76
A - B = 38
```

**Solution:**

1. Add both equations: 2A = 114
2. A = 114 / 2
3. **A = 19**

4. Substitute back: A + B = 76
5. B = 76 - 19
6. **B = 57**

**Final Answer:** A = 19, B = 57

---

## Section 2: Problem Solving (30 points total)

### 2.1 Debugging Third-Party API Failures

**Step 1 – Reproduce and Observe the Error**

First, I would reproduce the failure locally to confirm the issue. I would run the application and check the VS Code terminal logs and debug console to see the exact error message returned by the third-party API. Using the VS Code Debugger, I would set breakpoints near the API request code to inspect variables, request payloads, and responses.

**Step 2 – Verify the Recent Changes with Git**

Next, I would use Git in VS Code to check recent commits (git log) to determine whether the issue started after a code change or dependency update. If needed, I would temporarily check out an older commit or branch to compare behavior and confirm whether the failure is caused internally or by the external API.

**Step 3 – Analyze the API Integration**

I would review the API request structure (URL, headers, parameters, and response format) in the code. Then I would compare it with the latest third-party API documentation to identify possible breaking changes such as renamed fields, new authentication requirements, or modified endpoints.

**Step 4 – Test the API Independently**

To isolate the problem, I would test the API request outside the application using tools like Postman or curl. If the request fails or returns a different response format, it confirms that the issue is due to the API change rather than internal application logic.

**Step 5 – Implement and Debug the Fix**

After identifying the root cause, I would update the code to match the new API specification. I would use VS Code debugging tools again to step through the updated logic and confirm the request and response are handled correctly.

**Step 6 – Commit and Document the Fix**

Finally, I would commit the fix using Git, write a clear commit message explaining the API change, and update documentation or comments so future developers understand the dependency change and how it was resolved.

---

### 2.2 NestJS Image Upload System

**Prompt:** Generate a NestJS service and controller for handling user image uploads.

**Requirements:**

1. Use NestJS with TypeScript
2. Accept image uploads using Multer (Multer in NestJS is a middleware used to handle file uploads in your API)
3. Validate that the uploaded file type is JPEG or PNG
4. Ensure the file size does not exceed 5MB
5. Store the image metadata (filename, size, tags, upload date) in a cloud database
6. Return a JSON response containing:
   - Upload status
   - Link to the stored image (cloud storage URL)

**Structure the code with:**

- UploadController
- UploadService
- DTO for upload response
- Proper error handling for invalid format or oversized files

**Use libraries:**

- @nestjs/platform-express (Multer)
- file-type or mimetype validation

---

**Explanation (Why This Prompt Is Efficient)**

This prompt is efficient because it clearly specifies the framework (NestJS), architecture (controller, service, DTO), and required libraries, which helps the AI generate code that fits directly into a NestJS project. The requirements also define file validation rules and upload limits, reducing ambiguity in the generated logic. By including a placeholder for the AI tagging model, the code can be prototyped quickly without needing a real ML model immediately. This structure allows developers to rapidly test and expand the feature in a real NestJS backend.

## Section 3: AI & Modern Tech Trends (20 points total)

### 3.1 Database Migration Strategy

If a project changes from SQL to MongoDB during development, I would first review the official MongoDB Documentation to understand key concepts like collections, documents, and schema design. I would also use AI tools such as ChatGPT to quickly compare SQL queries with MongoDB queries and generate example code. Next, I would build a small prototype to practice CRUD operations and test how the new database integrates with the backend framework. At the same time, I would communicate with the team through meetings or chat to clarify data structure changes and migration strategies. This collaboration ensures everyone understands the new database design and helps the team transition smoothly without blocking development.

---

## Section 4: Coding (15 points total)

### 4.1 Email Domain Extraction

```typescript
function extractEmailDomain(email: string): string {
  // Allowed characters check
  const emailRegex = /^[A-Za-z0-9.-]+@[A-Za-z0-9.-]+$/;

  // Must match allowed characters
  if (!emailRegex.test(email)) {
    return "Invalid";
  }

  // Must contain exactly one "@"
  const parts = email.split("@");
  if (parts.length !== 2) {
    return "Invalid";
  }

  const local = parts[0];
  const domain = parts[1];

  // Local and domain must not be empty
  if (!local || !domain) {
    return "Invalid";
  }

  return domain;
}

console.log(extractEmailDomain("John.Smith@example.com"));
// Output: example.com

console.log(extractEmailDomain("user123@test-domain.org"));
// Output: test-domain.org

console.log(extractEmailDomain("invalid-email.com"));
// Output: Invalid

console.log(extractEmailDomain("user@@example.com"));
// Output: Invalid
```

## Section 5: Communication (15 points total)

Prompt engineering is the skill of writing clear and effective instructions for AI systems so they produce useful results. A simple analogy is ordering food at a restaurant 🍽️. If you just say “give me food,” the waiter may bring something you don’t want. But if you say “I want a grilled chicken sandwich with no onions,” you will get exactly what you need. In the same way, developers must give precise instructions (prompts) to AI tools so the output is accurate and helpful.

For a non-technical stakeholder like a project manager, prompt engineering helps teams work faster and more efficiently. Developers can use AI tools to generate code, explain complex bugs, or suggest better solutions by writing well-structured prompts. In 2026, many development tools integrate AI assistants, so knowing how to communicate clearly with AI becomes an important productivity skill.

It also connects to problem-solving. When developers break a problem into clear steps and describe it properly in a prompt, the AI can generate better suggestions or code. This means developers spend less time searching for solutions and more time building features, improving both speed and quality of software development.
