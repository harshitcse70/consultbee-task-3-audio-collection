# Task 5 — Production Scaling Plan

## Scenario

The current audio collection app is a lightweight prototype that allows gig workers to enter their name and phone number, record or upload audio, and submit the recording.

If the application were launched to **5,000 gig workers over a single weekend**, the prototype architecture would need to be changed before production use.

The main concerns would be **storage, concurrent uploads, failures, duplicate submissions, application capacity, database reliability, cost, and monitoring**.

The goal would not be to introduce unnecessary complexity, but to remove the major single points of failure and make the system capable of handling traffic spikes safely.

---

## Table of Contents

1. [What Would Break First](#1-what-would-break-first)
2. [Changes Before Launch](#2-changes-i-would-make-before-launch)
3. [Prevent Duplicate Submissions](#3-prevent-duplicate-submissions)
4. [Scale the Application Layer](#4-scale-the-application-layer)
5. [Database Improvements](#5-database-improvements)
6. [Background Processing](#6-background-processing)
7. [Cost Management](#7-cost-management)
8. [Monitoring and Operations](#8-monitoring-and-operations)
9. [Proposed Production Architecture](#9-proposed-production-architecture)
10. [Launch Priorities](#10-launch-priorities)
11. [What I Would Not Do Immediately](#11-what-i-would-not-do-immediately)
12. [Final Assessment](#12-final-assessment)

---

## 1. What Would Break First

### 1.1 Local Audio Storage

The current prototype stores uploaded recordings on the application's local filesystem.

At 5,000 workers, this could become a major limitation because:

- Audio files could consume disk space quickly.
- Files are tied to a single application server.
- A server failure could result in lost recordings.
- Multiple application instances would not automatically share the same files.
- Backups and retention would become difficult to manage.

### 1.2 Concurrent Uploads

Thousands of workers could submit recordings within a short period.

If every audio file passes through a single application server, the server could become a bottleneck due to:

- Network bandwidth
- Disk I/O
- CPU and memory usage
- Long-running HTTP requests
- Maximum concurrent connections

### 1.3 Application Capacity

A single application instance would become a single point of failure.

A sudden traffic spike could cause slow requests, timeouts, or failed submissions.

### 1.4 Failed Uploads

Gig workers may use mobile networks, which can be unreliable.

An upload could fail because of:

- Network interruption
- Browser closure
- Request timeout
- Server failure
- Temporary storage failure

The system must be able to recover without forcing the worker to restart unnecessarily.

### 1.5 Duplicate Submissions

A worker could click Submit twice or retry after a timeout even though the first request succeeded.

Without duplicate protection, the same recording could be stored multiple times.

### 1.6 Database Load

The database would receive many concurrent submissions and status updates.

Poor connection management, missing indexes, or excessive writes could cause the database to become another bottleneck.

---

## 2. Changes I Would Make Before Launch

### 2.1 Move Audio to Object Storage

I would move audio files away from the application's local filesystem to durable object storage such as **Amazon S3 or an equivalent service**.

The database would store metadata such as:

- Worker ID
- Submission ID
- Audio object key
- File size
- Upload status
- Timestamp
- Processing status

The actual audio binary would remain in object storage.

**Benefits:**

- Durable storage
- Easy horizontal scaling
- Better backup and lifecycle management
- Storage independent of application servers
- Multiple application instances can access the same recordings

### 2.2 Use Direct/Presigned Uploads

Instead of sending large audio files through the application server:

```text
Worker Browser
      |
      v
Application/API
      |
      v
Presigned Upload URL
      |
      v
Object Storage
```

The application would generate a short-lived presigned upload URL.

The browser could then upload the recording directly to object storage.

This prevents the application servers from becoming the bottleneck for large audio uploads.

For larger recordings, resumable or multipart uploads could also be introduced.

### 2.3 Add Upload Validation

Before accepting a recording, the system should validate:

- Allowed audio formats
- Maximum file size
- Maximum recording duration
- Required worker information
- Submission identifier

This prevents unexpectedly large or invalid files from consuming resources.

### 2.4 Add Reliable Upload States

Instead of treating a submission as simply successful or failed, I would track its state.

Example:

```text
PENDING
   |
   v
UPLOADING
   |
   v
UPLOADED
   |
   v
PROCESSING
   |
   v
COMPLETED
```

A failure could move the submission to:

```text
FAILED
```

This makes it possible to retry failed operations and understand what happened to each submission.

### 2.5 Handle Retries Safely

Temporary failures should not result in lost recordings.

The system should support:

- Request timeouts
- Retry mechanisms
- Failed-upload recovery
- Clear error messages
- Server-side status tracking
- Background processing for expensive audio operations

Retries must be designed to be safe so that retrying a request does not automatically create another recording.

---

## 3. Prevent Duplicate Submissions

Duplicate submissions are especially important because users may retry when they do not receive a response.

I would generate a unique submission or recording ID for every intended submission.

For example:

```text
worker_id + task_id + recording_id
```

could identify a unique submission.

The backend would use this identifier as an idempotency key.

If the same request arrives twice, the system would return the existing submission status instead of creating another database record or recording.

The database should also enforce appropriate unique constraints as a second layer of protection.

---

## 4. Scale the Application Layer

Instead of running one application server:

```text
Workers
   |
   v
One Application Server
```

I would use multiple application instances behind a load balancer:

```text
                 Workers
                    |
                    v
              Load Balancer
               /          \
              v            v
        App Instance 1   App Instance 2
              \            /
               \          /
                  Backend
```

This provides:

- Horizontal scaling
- Better availability
- Traffic distribution
- Failure isolation
- Ability to add instances during traffic spikes

The application should remain stateless wherever possible so that any request can be handled by any healthy instance.

---

## 5. Database Improvements

The database should store submission metadata rather than large audio files.

Before launch I would use:

- Production-grade database
- Connection pooling
- Proper indexes
- Transactions
- Unique constraints
- Automated backups
- Monitoring
- Recovery procedures

Important indexes would be added for fields frequently used to find submissions or check their status.

---

## 6. Background Processing

Audio processing should not unnecessarily block the user's upload request.

For example:

```text
Upload
   |
   v
Object Storage
   |
   v
Processing Queue
   |
   v
Background Worker
   |
   v
Audio Processing
```

This allows the upload to complete quickly while processing happens asynchronously.

If audio processing fails, the job can be retried without requiring the worker to upload the recording again.

---

## 7. Cost Management

At 5,000 workers, cost would depend on the amount and duration of audio submitted.

Major cost drivers would include:

- Object storage
- Data transfer
- Application compute
- Database usage
- Background processing
- Logs
- Backups

Before launch I would control costs by:

- Setting maximum recording duration
- Setting maximum file size
- Using appropriate audio compression
- Applying object-storage lifecycle policies
- Archiving or deleting old recordings according to retention requirements
- Avoiding unnecessary downloads
- Monitoring storage growth
- Monitoring bandwidth
- Setting cloud budget alerts
- Scaling compute according to actual demand

The objective would be to handle the weekend peak without permanently over-provisioning infrastructure.

---

## 8. Monitoring and Operations

Before launch, I would add monitoring for:

### 8.1 Application

- Request latency
- Error rate
- Concurrent requests
- CPU usage
- Memory usage

### 8.2 Uploads

- Upload success rate
- Upload failure rate
- Upload duration
- Active uploads
- Average audio file size
- Failed retries

### 8.3 Database

- Connection usage
- Query latency
- Error rate
- Storage usage

### 8.4 Storage

- Number of recordings
- Total storage consumed
- Storage growth rate
- Failed uploads

### 8.5 Processing

- Processing queue size
- Processing failures
- Processing duration
- Retry count

### 8.6 Alerts

Alerts should be configured for critical conditions such as:

- High application error rate
- Increasing upload failures
- Database problems
- Storage exhaustion
- Unusual traffic spikes
- Processing backlog

Each submission should have a unique identifier that can be included in logs so that a failed worker submission can be traced through the system.

---

## 9. Proposed Production Architecture

```text
                         5,000 Gig Workers
                                |
                                v
                         Load Balancer
                                |
                  +-------------+-------------+
                  |                           |
                  v                           v
            Application/API 1          Application/API 2
                  |                           |
                  +-------------+-------------+
                                |
                   +------------+------------+
                   |                         |
                   v                         v
              Production DB          Presigned Upload
              (Metadata)                    |
                                            v
                                     Object Storage
                                      (Audio Files)
                                            |
                                            v
                                    Processing Queue
                                            |
                                            v
                                    Background Worker
                                            |
                                            v
                                      Audio Processing
```

The key design principle is to keep **application compute, metadata storage, audio storage, and background processing independent**.

This means each component can scale independently and a failure in one component is less likely to bring down the entire application.

---

## 10. Launch Priorities

I would implement the production changes in this order:

1. Move audio files from local storage to durable object storage.
2. Implement direct/presigned and reliable uploads.
3. Add file-size, duration, and format validation.
4. Implement idempotency and duplicate-submission protection.
5. Add explicit upload and processing states.
6. Add retry and failure recovery mechanisms.
7. Move to a production-grade database with backups and connection management.
8. Run multiple application instances behind a load balancer.
9. Move expensive audio processing to background workers.
10. Add monitoring, logging, alerts, and cost controls.
11. Load-test the complete submission flow before the weekend launch.

---

## 11. What I Would Not Do Immediately

I would avoid introducing unnecessary infrastructure simply because the application is expected to scale.

For 5,000 workers, I would first identify the actual bottlenecks through load testing and monitoring.

I would not automatically introduce Kubernetes, microservices, or a large distributed system unless the expected workload and operational requirements justified them.

The priority would be **reliability, durable storage, safe uploads, duplicate prevention, observability, and predictable cost**.

---

## 12. Final Assessment

The current Task 3 application is suitable as a functional prototype and local demonstration.

For a real 5,000-worker weekend launch, the first major changes would be moving audio from local disk to object storage, separating large file uploads from application servers, making submissions idempotent, handling failures and retries, scaling the application layer, and adding monitoring and cost controls.

The overall goal is to make sure that a temporary traffic spike, failed network request, duplicate submission, or individual server failure does not result in **lost recordings or an unavailable service**.