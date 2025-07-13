# Contributing Guidelines

Thank you for your interest in contributing to the Top Streaming Services Data Portugal project! This document provides guidelines and information for contributors.

## 🤝 Ways to Contribute

### Reporting Issues
- **Bug Reports**: Found a bug? Please create an issue with detailed information
- **Feature Requests**: Have an idea for improvement? We'd love to hear it
- **Documentation**: Help improve or translate documentation
- **Code**: Submit pull requests for bug fixes or new features

### What We're Looking For

- Bug fixes and performance improvements
- Support for additional streaming platforms
- Enhanced error handling and logging
- Code quality improvements
- Documentation updates
- Test coverage improvements

## 🚀 Getting Started

### Prerequisites
- Python 3.13+ (recommended)
- Git
- GitHub account
- Basic understanding of web scraping and APIs

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/top-streaming-services-data-portugal.git
   cd top-streaming-services-data-portugal
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment**
   ```bash
   cp .env.example .env  # Create from template
   # Edit .env with your Trakt credentials
   ```

4. **Test Your Setup**
   ```bash
   python top_pt_stream_services.py
   ```

## 📝 Development Guidelines

### Code Style
- Follow [PEP 8](https://pep8.org/) Python style guidelines
- Use descriptive variable and function names
- Add docstrings for functions and classes
- Keep functions focused and reasonably sized

### Error Handling
- Use appropriate exception handling
- Provide meaningful error messages
- Log errors appropriately using the existing logging framework

### Adding New Streaming Services

When adding support for a new streaming platform:

1. **Add URL Configuration**
   ```python
   # Add to global variables section
   top_newservice_url = "https://flixpatrol.com/top10/newservice/portugal/"
   ```

2. **Create List Data Structures**
   ```python
   trakt_newservice_movies_list_data = {
       "name": "Top Portugal NewService Movies",
       "description": "List that contains the top 10 movies on NewService Portugal right now, updated daily",
       "privacy": "public",
       "display_numbers": True
   }
   ```

3. **Add to Main Processing Loop**
   ```python
   # In main() function
   top_newservice_movies = scrape_top10(top_newservice_url, top_movies_section)
   ```

4. **Update Documentation**
   - Add the new service to README.md
   - Update feature lists and examples

### Testing

While this project doesn't have formal automated tests, please:

1. **Manual Testing**
   - Test with different environment configurations
   - Verify scraping works correctly
   - Check Trakt list updates

2. **Error Scenarios**
   - Test with invalid credentials
   - Test with network issues
   - Test with malformed FlixPatrol responses

## 📋 Pull Request Process

### Before Submitting

1. **Check Existing Issues**: Look for related issues or PRs
2. **Test Thoroughly**: Ensure your changes work as expected
3. **Update Documentation**: Update README.md and other docs as needed
4. **Follow Code Style**: Ensure your code follows project conventions

### PR Guidelines

1. **Clear Title**: Use a descriptive title
2. **Detailed Description**: Explain what your PR does and why
3. **Link Issues**: Reference any related issues
4. **Small Changes**: Keep PRs focused and reasonably sized

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring

## Testing
- [ ] Tested manually
- [ ] Works with existing configuration
- [ ] No breaking changes

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] No new warnings or errors
```

## 🔍 Code Review Process

### What We Look For

- **Functionality**: Does the code work as intended?
- **Quality**: Is the code clean, readable, and maintainable?
- **Performance**: Are there any performance implications?
- **Security**: Are there any security concerns?
- **Documentation**: Is the code properly documented?

### Review Timeline

- Initial review within 3-5 business days
- Follow-up reviews within 1-2 business days
- Merge after approval and passing checks

## 🐛 Issue Guidelines

### Bug Reports

Please include:
- **Description**: Clear description of the bug
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**: Python version, OS, dependencies
- **Logs**: Relevant error messages or logs

### Feature Requests

Please include:
- **Description**: Clear description of the feature
- **Use Case**: Why is this feature needed?
- **Implementation Ideas**: Any thoughts on implementation
- **Alternatives**: Any alternative solutions considered

## 🏷️ Labels and Workflow

### Issue Labels
- `bug`: Something isn't working
- `enhancement`: New feature or improvement
- `documentation`: Documentation improvements
- `good-first-issue`: Good for newcomers
- `help-wanted`: Extra attention needed

### Project Workflow
1. **Issues**: Create or find an issue to work on
2. **Assignment**: Get assigned or assign yourself
3. **Development**: Create a branch and implement changes
4. **Testing**: Test your changes thoroughly
5. **PR**: Submit a pull request
6. **Review**: Participate in code review
7. **Merge**: Changes get merged after approval

## 💡 Tips for Contributors

### First-Time Contributors
- Start with `good-first-issue` labeled issues
- Ask questions if you're unsure about anything
- Don't be afraid to make mistakes - we're here to help!

### Regular Contributors
- Help review other people's PRs
- Suggest improvements to documentation
- Help mentor new contributors

### Advanced Contributors
- Consider becoming a maintainer
- Help with project planning and roadmap
- Implement complex features or refactoring

## 📞 Communication

### Where to Ask Questions
- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For general questions and ideas
- **Pull Request Comments**: For code-specific questions

### Response Times
- We aim to respond to issues within 3-5 business days
- PRs are typically reviewed within 3-5 business days
- Urgent issues will be prioritized

## 🔐 Security

### Reporting Security Issues
- **DO NOT** create public issues for security vulnerabilities
- Email maintainers directly for security concerns
- Provide detailed information about the vulnerability

### Security Guidelines
- Never commit API keys or secrets
- Use environment variables for sensitive data
- Follow security best practices in code

## 📜 License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to Top Streaming Services Data Portugal! 🎉