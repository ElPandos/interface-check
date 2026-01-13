> ## Summary

I've researched current code performance optimization best practices and created comprehensive documentation. The research revealed significant evolution toward data-driven optimization approaches with modern APM tools and systematic methodologies.

Key findings:
- Profile-first methodology is essential - companies see 20-30% typical speedups through data-driven optimization
- Algorithm selection has the highest performance impact - choosing O(n log n) over O(n²) provides exponential improvements  
- Modern APM tools with AI-powered analytics are becoming standard (Dynatrace, New Relic, Middleware.io)
- Database optimization through proper indexing can reduce query times from seconds to milliseconds
- Performance optimization must be integrated into development workflows, not treated as an afterthought

File saved: .kiro/research/2026-01-13/best-practices/code-performance-optimization.md

The steering document covers core optimization principles, modern techniques, monitoring tools, implementation best practices, platform-specific optimizations, and success metrics based on current industry research.

## Synchronization Report (Tier 2)

### Primary File Updated
- Path: .kiro/steering/code-performance-optimization_best-practices.md
- Change type: creation
- Impact: additive

### Related Files Identified
- .kiro/steering/code-quality_patterns.md - no change needed (focuses on maintainability vs performance)
- .kiro/steering/development-standards_patterns.md - no change needed (covers broader development practices)
- .kiro/steering/testing_patterns.md - no change needed (performance testing covered in both appropriately)

### Files Intentionally Not Checked
- Other pattern files (focus on different domains like UI, security, etc.)