# Discovery Questions - Selective CLAUDE.md Deployment

**Phase**: Discovery (2 of 5)
**Questions**: 5 yes/no questions with smart defaults

## Q1: Should we implement automated directory analysis to identify high-value directories?
**Default if unknown:** Yes (automation reduces manual effort and ensures consistent criteria application)
**Reasoning**: With 254+ directories, manual evaluation would be time-consuming and error-prone. Automated analysis can apply consistent criteria (file count ≥5, complexity indicators, modification frequency) to identify deployment targets.

## Q2: Should we maintain the hierarchical inheritance system from the root CLAUDE.md?
**Default if unknown:** Yes (proven successful in POC and aligns with industry best practices)
**Reasoning**: The hierarchical reference system has been validated with excellent quality scores (9.8/10) and follows patterns from major projects like Kubernetes and React.

## Q3: Will the selective deployment require different templates based on directory complexity?
**Default if unknown:** Yes (different directory types need different levels of documentation detail)
**Reasoning**: POC showed that components, tests, commands, and infrastructure directories need different architectural guidance and content analysis depth.

## Q4: Should we implement quality gates to prevent deployment of low-value CLAUDE.md files?
**Default if unknown:** Yes (quality over quantity approach requires validation checkpoints)
**Reasoning**: To maintain the 95% relevance target and avoid documentation overhead, validation gates ensure only directories meeting value criteria receive CLAUDE.md files.

## Q5: Will this deployment require coordination with the existing development workflow?
**Default if unknown:** Yes (CLAUDE.md files become part of developer onboarding and reference system)
**Reasoning**: Content-aware CLAUDE.md files will be used for developer onboarding, directory navigation, and development guidance, requiring integration with existing workflows and tooling.

---

**Next**: Answer all questions above to proceed to context gathering phase.