# raGROW User Guide

## Maker
1. Submit ADD / MODIFY / DELETE mutation
2. Mutation enters queue
3. Await checker approval

## Checker
1. Review queued mutations
2. Reject individual mutations if needed
3. Approve batch
4. System rebuilds corpus and creates new STAGING version
5. Promote version to ACTIVE if validated
