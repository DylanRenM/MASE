'use strict';

const fs = require('fs');
const path = require('path');

function classify(errors) {
  const text = errors.join('\n').toLowerCase();
  if (!text) return 'unknown';
  if (/econnrefused|net::err_|webserver|timed out waiting for.*server|executable doesn't exist|playwright install/.test(text)) return 'environment';
  if (/fixture|seed|database.*schema|test data/.test(text)) return 'test-data';
  if (/strict mode violation|selector|locator.*resolved to/.test(text)) return 'test';
  if (/expect\(|assert|expected|received/.test(text)) return 'product';
  return 'unknown';
}

class MaseReporter {
  constructor() {
    this.results = [];
  }

  onTestEnd(test, result) {
    this.results.push({
      id: test.id || test.title,
      title: typeof test.titlePath === 'function' ? test.titlePath().join(' › ') : test.title,
      status: result.status,
      retry: Number(result.retry || 0),
      errors: (result.errors || []).map(error => error.message || String(error)),
      artifacts: (result.attachments || []).map(item => item.path).filter(Boolean),
    });
  }

  onEnd(result) {
    const output = process.env.MASE_TEST_DIAGNOSTIC_PATH;
    if (!output) return;
    const retries = this.results.filter(item => item.retry > 0);
    const failures = this.results.filter(item => !['passed', 'skipped'].includes(item.status));
    const finalPassed = result.status === 'passed';
    const flaky = finalPassed && retries.length > 0;
    const errors = failures.flatMap(item => item.errors);
    const payload = {
      schema: 'mase-test-diagnostic/v1',
      attempts: Math.max(1, ...this.results.map(item => item.retry + 1)),
      first_attempt_result: flaky || !finalPassed ? 'failed' : 'passed',
      final_result: finalPassed ? 'passed' : 'failed',
      ...(flaky || !finalPassed ? { classification: flaky ? 'flaky' : classify(errors) } : {}),
      failed_tests: [...new Set((flaky ? retries : failures).map(item => item.title || item.id))],
      artifacts: [...new Set(this.results.flatMap(item => item.artifacts))],
    };
    fs.mkdirSync(path.dirname(output), { recursive: true });
    fs.writeFileSync(output, JSON.stringify(payload, null, 2) + '\n', 'utf8');
  }
}

module.exports = MaseReporter;
module.exports.classify = classify;
