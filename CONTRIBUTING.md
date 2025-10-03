# 🤝 Contributing to Smart Contract Rewriter Platform

Thank you for your interest in contributing to the Smart Contract Rewriter Platform! This project welcomes contributions from developers of all skill levels.

## 🎯 **Ways to Contribute**

### **💻 Code Contributions**
- 🐛 **Bug fixes** - Help resolve issues and improve stability
- ✨ **New features** - Implement enhancements and new capabilities  
- 📈 **Performance improvements** - Optimize code and infrastructure
- 🧪 **Tests** - Improve test coverage and quality
- 📖 **Documentation** - Enhance guides and API documentation

### **📋 Non-Code Contributions**
- 🐛 **Bug reports** - Help identify issues and edge cases
- 💡 **Feature requests** - Suggest new functionality
- 📝 **Documentation improvements** - Fix typos, clarify instructions
- 🎨 **UI/UX feedback** - Improve user experience
- 🌍 **Translations** - Internationalization support

---

## 🚀 **Getting Started**

### **1. Fork & Clone**
```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/smart-contract-rewriter.git
cd smart-contract-rewriter

# Add upstream remote
git remote add upstream https://github.com/davidx345/smart-contract-rewriter.git
```

### **2. Set Up Development Environment**
```bash
# Follow the setup guide
cp .env.example .env
# Edit .env with your configuration

# Start development environment
docker-compose up -d

# Or set up locally
cd backend && pip install -r requirements.txt
cd frontend && npm install
```

### **3. Create Feature Branch**
```bash
# Create and switch to feature branch
git checkout -b feature/your-feature-name

# Keep your branch updated
git fetch upstream
git rebase upstream/main
```

---

## 📝 **Development Guidelines**

### **🎨 Code Style**

#### **Python (Backend)**
- Follow **PEP 8** style guidelines
- Use **Black** for code formatting
- Use **type hints** for all functions
- Maximum line length: **88 characters**

```python
# Good example
def analyze_contract(
    source_code: str, 
    language: str = "solidity"
) -> Dict[str, Any]:
    """Analyze smart contract for vulnerabilities.
    
    Args:
        source_code: The contract source code
        language: Programming language (default: solidity)
        
    Returns:
        Analysis results with scores and suggestions
    """
    # Implementation here
    pass
```

#### **TypeScript (Frontend)**
- Use **TypeScript** strict mode
- Follow **Airbnb style guide**
- Use **Prettier** for formatting
- Prefer **functional components** with hooks

```typescript
// Good example
interface ContractAnalysisProps {
  sourceCode: string;
  onAnalysisComplete: (result: AnalysisResult) => void;
}

const ContractAnalysis: React.FC<ContractAnalysisProps> = ({
  sourceCode,
  onAnalysisComplete,
}) => {
  // Component implementation
};
```

### **🧪 Testing Requirements**

#### **Backend Tests**
```bash
# Run tests before submitting
cd backend
pytest tests/ -v --cov=app

# Ensure coverage > 80%
pytest --cov=app --cov-report=html tests/
```

#### **Frontend Tests**
```bash
# Unit tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

### **📖 Documentation**

- **Docstrings** for all functions and classes
- **README updates** for new features
- **API documentation** for new endpoints
- **Inline comments** for complex logic

---

## 🔄 **Contribution Workflow**

### **1. Issue First Approach**
- 🔍 **Check existing issues** before starting work
- 💬 **Comment on issues** to claim them
- 📝 **Create new issues** for bugs or features
- 🏷️ **Use appropriate labels** (bug, enhancement, documentation)

### **2. Branch Naming Convention**
```bash
feature/add-gas-optimization     # New features
bugfix/fix-contract-parsing      # Bug fixes
docs/update-setup-guide         # Documentation
refactor/optimize-ai-service    # Code refactoring
test/add-integration-tests      # Testing improvements
```

### **3. Commit Message Format**
Follow **Conventional Commits** specification:

```bash
# Format
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]

# Examples
feat(ai): add gas optimization analysis
fix(auth): resolve JWT token expiration issue
docs(setup): update Docker installation steps
test(api): add contract upload endpoint tests
refactor(db): optimize query performance
```

### **4. Pull Request Process**

#### **Before Submitting**
- ✅ All tests pass locally
- ✅ Code follows style guidelines
- ✅ Documentation updated
- ✅ No merge conflicts with main branch

#### **PR Description Template**
```markdown
## 🎯 Description
Brief description of changes

## 🔧 Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## 🧪 Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## 📝 Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
```

---

## 🏷️ **Issue Labels**

| Label | Description | Example |
|-------|-------------|---------|
| `bug` | Something isn't working | API returning 500 error |
| `enhancement` | New feature or request | Add smart contract deployment |
| `documentation` | Improvements or additions | Update setup guide |
| `good first issue` | Good for newcomers | Fix typo in README |
| `help wanted` | Extra attention needed | Complex algorithm optimization |
| `priority: high` | Critical issues | Security vulnerability |
| `priority: low` | Nice to have | UI polish |

---

## 🎖️ **Recognition**

### **Contributors Hall of Fame**

#### **🚀 Core Contributors**
- **David (@davidx345)** - Project founder and lead developer

#### **💻 Code Contributors**
*Your name could be here! Make a contribution to get listed.*

#### **📝 Documentation Contributors**
*Help improve our docs and see your name here!*

#### **🐛 Bug Hunters**
*Found and reported bugs? You'll be recognized here!*

### **Contribution Rewards**
- 🏆 **GitHub profile badge** for contributors
- 📜 **Certificate of contribution** for significant contributions
- 🎁 **Swag** for major feature contributions
- 💼 **LinkedIn recommendation** for outstanding contributors

---

## 🚨 **Code of Conduct**

### **Our Pledge**
We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### **Our Standards**
**Positive behavior includes:**
- ✅ Using welcoming and inclusive language
- ✅ Being respectful of differing viewpoints
- ✅ Gracefully accepting constructive criticism
- ✅ Focusing on what is best for the community

**Unacceptable behavior includes:**
- ❌ Use of sexualized language or imagery
- ❌ Trolling, insulting, or derogatory comments
- ❌ Personal or political attacks
- ❌ Harassment of any kind

### **Enforcement**
Report unacceptable behavior to: conduct@smartcontract-platform.dev

---

## 💡 **Development Tips**

### **🔧 Local Development**
```bash
# Quick development setup
make dev-setup  # If Makefile exists
# or
docker-compose up -d db redis
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
```

### **🐛 Debugging**
```bash
# Backend debugging
export DEBUG=true
python -m debugpy --wait-for-client --listen 5678 -m uvicorn app.main:app --reload

# Frontend debugging
npm run dev -- --debug
```

### **📊 Performance Profiling**
```bash
# Backend profiling
pip install py-spy
py-spy top --pid <backend_pid>

# Frontend profiling
npm run build:analyze
```

---

## 🎯 **Current Priorities**

### **🔥 High Priority**
- [ ] Improve AI analysis accuracy
- [ ] Add smart contract deployment feature
- [ ] Enhance security scanning
- [ ] Performance optimization

### **📈 Medium Priority**
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Team collaboration features
- [ ] API rate limiting improvements

### **💡 Ideas Welcome**
- [ ] Mobile app development
- [ ] Browser extension
- [ ] VS Code extension
- [ ] Slack/Discord integration

---

## 📞 **Getting Help**

### **💬 Communication Channels**
- **GitHub Issues** - Technical problems and feature requests
- **GitHub Discussions** - General questions and community chat
- **Discord** - Real-time chat (link in README)
- **Email** - contributors@smartcontract-platform.dev

### **📚 Resources**
- [Setup Guide](docs/setup-guide.md)
- [Architecture Documentation](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Security Guidelines](docs/security.md)

---

<div align="center">

**🎉 Thank you for contributing to the Smart Contract Rewriter Platform!**

Every contribution, no matter how small, makes a difference. Together, we're building the future of smart contract development tools.

[**🌟 Start Contributing**](https://github.com/davidx345/smart-contract-rewriter/issues/new/choose) • [**🍴 Fork the Repo**](https://github.com/davidx345/smart-contract-rewriter/fork) • [**💬 Join Discussion**](https://github.com/davidx345/smart-contract-rewriter/discussions)

</div>