# Changelog

All notable changes to the Top Streaming Services Data Portugal project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive project documentation
- Setup guide with step-by-step instructions
- API documentation with endpoint details
- Contributing guidelines for developers
- Environment configuration template
- Troubleshooting guide

### Changed
- Enhanced README.md with detailed feature descriptions
- Improved code comments and documentation
- Better error handling and logging descriptions

## [1.0.0] - 2024-01-15

### Added
- Initial project release
- Support for multiple streaming platforms:
  - Netflix (Movies, TV Shows, Kids content)
  - HBO Max (Movies, TV Shows)
  - Disney+ (Overall rankings)
  - Apple TV+ (Movies, TV Shows)
  - Amazon Prime Video (Movies, TV Shows)
- Automated web scraping from FlixPatrol
- Trakt.tv API integration for list management
- GitHub Actions automation with cron scheduling
- OAuth token refresh mechanism
- Comprehensive logging system
- Retry logic for API requests
- Error handling for network and API issues

### Core Features
- Daily automated updates (4 times per day)
- Public Trakt lists with ranking preservation
- Support for optional kids content
- Debug mode for development
- Environment-based configuration

### Infrastructure
- GitHub Actions workflow for automation
- Python 3.13 compatibility
- Minimal dependencies (requests, beautifulsoup4, python-dotenv)
- Cross-platform compatibility

---

## Version History Notes

### Versioning Strategy
- **Major version** (X.0.0): Breaking changes, major feature additions
- **Minor version** (0.X.0): New features, improvements, non-breaking changes
- **Patch version** (0.0.X): Bug fixes, documentation updates, minor improvements

### Release Process
1. Update CHANGELOG.md with new version details
2. Tag release with version number
3. Update documentation if needed
4. Announce release in GitHub Discussions

### Maintenance Schedule
- **Dependencies**: Updated monthly for security and compatibility
- **Documentation**: Updated with each feature release
- **API Compatibility**: Monitored continuously for breaking changes

---

## Future Roadmap

### Planned Features
- [ ] Support for additional streaming platforms
- [ ] Configurable update schedules
- [ ] Email notifications for failures
- [ ] Historical data tracking
- [ ] List comparison and analytics
- [ ] Multi-language support
- [ ] API rate limiting improvements
- [ ] Enhanced error recovery
- [ ] Docker containerization
- [ ] Database storage option

### Potential Integrations
- [ ] Plex integration
- [ ] Letterboxd sync
- [ ] IMDb list management
- [ ] Discord/Slack notifications
- [ ] Custom webhooks
- [ ] Statistics dashboard

---

For more detailed information about any release, please check the [GitHub Releases](https://github.com/pcarrasqueira/top-streaming-services-data-portugal/releases) page.