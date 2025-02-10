# ADR: Adoption of MinIO Instead of AWS S3 During Development


## Context

In this microservices ecosystem, AWS S3 is the default storage solution for handling file storage and retrieval. However, during development, I have opted to use MinIO instead of AWS S3. This decision was made to facilitate local development and testing while minimizing external dependencies.


## Decision
I have chosen MinIO as the temporary file storage solution during development instead of AWS S3.


## Rationale
### Ease of Substitution
- MinIO is fully compatible with AWS S3 API, making it easy to switch between the two without modifying application logic. 
- Using MinIO locally allows for faster iteration and debugging without requiring access to cloud infrastructure.

### Development Efficiency
- MinIO is allowing to run a local S3-compatible storage service, reducing the need for cloud resources. 
- Eliminates latency associated with remote storage and allows testing in isolated environments.

### Cost Reduction
- Running AWS S3 during development incurs unnecessary costs, whereas MinIO operates entirely on local infrastructure without additional expenses.

### Simplified Workflow
- Developer can work without requiring AWS credentials or network access to cloud services. 
- MinIO can be easily deployed via Docker, aligning with containerized development environments.

### Future Potential
- If MinIO proves to be efficient for local development, it may be standardized as the default local storage solution across other microservices. 
- If any limitations arise, switching back to AWS S3 remains an option without significant refactoring.


## Consequences
### Positive Outcomes
- Faster development cycles with reduced reliance on cloud services. 
- Cost savings by avoiding AWS usage for local testing.
- Easier debugging and isolation of storage-related issues.

### Challenges & Mitigation
- Inconsistency Across Environments: Differences between MinIO and AWS S3 may lead to discrepancies in behavior. However, these can be mitigated through integration testing in staging environments. 


## Status
Accepted – MinIO will be used as the file storage solution during development while monitoring its impact and evaluating its benefits for potential broader adoption.
