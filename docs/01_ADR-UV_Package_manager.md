# ADR: Adoption of UV Package Manager Instead of Poetry


## Context
In this microservices ecosystem, Poetry has been the default package manager for managing dependencies and virtual environments. However, for the specific microservice, I have opted to use UV instead of Poetry. This decision was made based on the desire to evaluate a new package management tool while keeping the scope of change minimal.


## Decision
I have chosen UV as the package manager for this particular microservice instead of Poetry.


## Rationale
### Evaluation of New Tools
- UV is a relatively new package manager that promises faster performance and a lightweight footprint.
- The microservice in question is the least complex in the architecture, making it an ideal candidate for testing a new tool without significant risk.

### Performance Considerations
- UV is designed with performance in mind, featuring a highly optimized dependency resolution process.
- Compared to Poetry, UV demonstrates faster package installation and environment setup times.

### Reduced Overhead
- UV requires fewer dependencies and has a simpler implementation compared to Poetry, making it potentially easier to maintain in the long run.
- It does not introduce additional virtual environment management beyond what is natively provided by Python.

### Compatibility with Existing Workflows
- UV integrates well with existing Python environments and does not impose significant changes to workflows.
- Dependency resolution and package management remain aligned with best practices while leveraging a modern, efficient approach.
- The latest update of PyCharm includes built-in support for UV, making it easier to integrate into development workflows.

### Future Potential
- If UV proves to be advantageous, it may be considered for broader adoption in other microservices.
- If any issues arise, reverting to Poetry is a feasible option given the isolated nature of this experiment.


## Consequences
### Positive Outcomes
- Faster dependency resolution and package installation. 
- Opportunity to validate the benefits of a modern package manager in a controlled environment.
- Potential reduction in build times and dependency management overhead.

### Challenges & Mitigation
- Inconsistency Across Microservices: UV differs from Poetry, which may lead to minor differences in dependency management. However, this is mitigated by the microservice’s limited scope and isolation.
- Learning Curve: Team members may need to familiarize themselves with UV, but its simplicity minimizes adoption friction.


## Status
Accepted – UV will be used for this specific microservice while monitoring its impact and evaluating its benefits for potential broader adoption.
