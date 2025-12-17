# Contributing to Data Engineering Tutorial

Thank you for your interest in contributing! This tutorial is designed to help people learn data engineering fundamentals.

## Ways to Contribute

### 1. Report Issues
- Bug reports
- Typos or unclear documentation
- Missing exercises or examples
- Feature requests

### 2. Improve Documentation
- Fix typos or grammar
- Add examples or explanations
- Improve existing modules
- Create new exercises

### 3. Add Code
- New exercise solutions
- Additional DAG examples
- Utility functions
- Performance improvements

### 4. Share Your Experience
- Write blog posts about the tutorial
- Share on social media
- Present at meetups
- Create video walkthroughs

## How to Contribute

### Reporting Issues

1. Check if the issue already exists
2. Use the issue template
3. Provide clear reproduction steps
4. Include error messages and screenshots

### Submitting Changes

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/data-engineering-tutorial.git
   cd data-engineering-tutorial
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add tests if applicable
   - Update documentation

4. **Test your changes**
   ```bash
   # Run tests
   pytest

   # Check code style
   black .
   flake8 .
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: your descriptive commit message"
   ```

6. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- **Python**: Follow PEP 8, use Black formatter
- **SQL**: Use uppercase keywords, meaningful names
- **Documentation**: Use clear, concise language
- **Comments**: Explain "why", not "what"

## Module Guidelines

When adding content to modules:

### Module Structure
```
module_X_topic/
├── README.md           # Main lesson
├── exercises/          # Practice problems
├── solutions/          # Solution code
└── assets/            # Images, diagrams
```

### Exercise Format
- Clear learning objectives
- Starter code provided
- Hints for guidance
- Complete solutions
- Real-world context

### Documentation Style
- Use practical examples
- Include code snippets
- Add diagrams where helpful
- Reference real-world scenarios
- Keep it beginner-friendly

## Review Process

1. **Automated Checks**
   - Code formatting (Black)
   - Linting (Flake8)
   - Tests (pytest)

2. **Manual Review**
   - Code quality
   - Documentation clarity
   - Educational value
   - Alignment with tutorial goals

3. **Feedback**
   - Reviewers will provide constructive feedback
   - Address comments or discuss alternatives
   - Update your PR based on feedback

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in relevant documentation

## Questions?

- Open a [Discussion](https://github.com/yourusername/data-engineering-tutorial/discussions)
- Reach out via email
- Join our community chat

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on learning and growth

Thank you for helping make data engineering education better for everyone!
