import fs from 'node:fs';
import path from 'node:path';

async function run() {
  const sarifPath = process.env.INPUT_SARIF_FILE;
  const title = process.env.INPUT_TITLE || 'Security Scan Report';
  const commentTag = process.env.INPUT_COMMENT_TAG || 'security-report';
  const token = process.env.INPUT_GITHUB_TOKEN || process.env.GITHUB_TOKEN;
  const failOnFindings = process.env.INPUT_FAIL_ON_FINDINGS === 'true';
  const shouldManageIssue = process.env.INPUT_MANAGE_ISSUE === 'true';
  const issueTitle = process.env.INPUT_ISSUE_TITLE || '[Security Audit] Active Vulnerabilities Detected';

  if (!sarifPath || !fs.existsSync(sarifPath)) {
    console.error(`SARIF file not found at path: ${sarifPath}`);
    process.exit(1);
  }

  const sarifRaw = fs.readFileSync(sarifPath, 'utf8');
  let sarif;
  try {
    sarif = JSON.parse(sarifRaw);
  } catch (err) {
    console.error(`Failed to parse SARIF JSON: ${err.message}`);
    process.exit(1);
  }

  const findings = [];
  const counts = { error: 0, warning: 0, note: 0 };

  const runs = sarif.runs || [];
  for (const run of runs) {
    const rulesMap = new Map();
    if (run.tool?.driver?.rules) {
      for (const rule of run.tool.driver.rules) {
        rulesMap.set(rule.id, rule);
      }
    }

    const results = run.results || [];
    for (const res of results) {
      let level = res.level;
      if (!level) {
        const rule = rulesMap.get(res.ruleId);
        level = rule?.defaultConfiguration?.level || 'warning';
      }

      const normalizedLevel = level === 'error' ? 'error' : level === 'note' ? 'note' : 'warning';
      counts[normalizedLevel]++;

      const location = res.locations?.[0]?.physicalLocation;
      const fileUri = location?.artifactLocation?.uri || 'unknown';
      const line = location?.region?.startLine || 1;
      const message = res.message?.text || 'No description provided';

      findings.push({
        ruleId: res.ruleId || 'Rule',
        level: normalizedLevel,
        file: fileUri,
        line,
        message: message.replace(/\r?\n|\r/g, ' ').slice(0, 150)
      });
    }
  }

  const total = counts.error + counts.warning + counts.note;
  const passed = total === 0;

  const statusHeader = passed
    ? `### ${title}: Passed ✅`
    : `### ${title}: ${total} issue${total === 1 ? '' : 's'} detected ⚠️`;

  let md = `<!-- security-report-${commentTag} -->\n`;
  md += `${statusHeader}\n\n`;

  md += `| Severity | Count |\n`;
  md += `| :--- | :--- |\n`;
  md += `| 🔴 Error / High | ${counts.error} |\n`;
  md += `| 🟡 Warning / Medium | ${counts.warning} |\n`;
  md += `| 🟢 Note / Low | ${counts.note} |\n`;
  md += `| **Total** | **${total}** |\n\n`;

  if (total === 0) {
    md += `> ✅ No security vulnerabilities or policy violations detected.\n`;
  } else {
    const maxDisplay = 25;
    const displayedFindings = findings.slice(0, maxDisplay);

    md += `<details>\n`;
    md += `<summary><b>View Findings (${displayedFindings.length}${total > maxDisplay ? ` of ${total}` : ''})</b></summary>\n\n`;
    md += `| Severity | Location | Rule | Description |\n`;
    md += `| :--- | :--- | :--- | :--- |\n`;

    for (const f of displayedFindings) {
      const icon =
        f.level === 'error'
          ? '🔴 Error'
          : f.level === 'note'
            ? '🟢 Note'
            : '🟡 Warning';
      md += `| ${icon} | \`${f.file}:${f.line}\` | \`${f.ruleId}\` | ${f.message} |\n`;
    }

    if (total > maxDisplay) {
      md += `\n*...and ${total - maxDisplay} more findings. Check the attached artifact for the full report.*\n`;
    }

    md += `\n</details>\n`;
  }

  md += `\n*Last updated: ${new Date().toISOString()}*\n`;

  const reportFile = path.resolve(process.cwd(), `${commentTag}-summary.md`);
  fs.writeFileSync(reportFile, md, 'utf8');

  if (process.env.GITHUB_STEP_SUMMARY) {
    fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, md + '\n\n');
    console.log('Appended summary to GITHUB_STEP_SUMMARY.');
  }

  if (process.env.GITHUB_OUTPUT) {
    fs.appendFileSync(process.env.GITHUB_OUTPUT, `total-findings=${total}\n`);
    fs.appendFileSync(process.env.GITHUB_OUTPUT, `report-file=${reportFile}\n`);
  }

  let prNumber = null;
  if (process.env.GITHUB_EVENT_PATH && fs.existsSync(process.env.GITHUB_EVENT_PATH)) {
    try {
      const eventData = JSON.parse(fs.readFileSync(process.env.GITHUB_EVENT_PATH, 'utf8'));
      prNumber = eventData.pull_request?.number || eventData.issue?.number || null;
    } catch (e) {
      console.warn(`Could not parse GITHUB_EVENT_PATH: ${e.message}`);
    }
  }

  const repo = process.env.GITHUB_REPOSITORY;
  if (prNumber && token && repo) {
    const marker = `<!-- security-report-${commentTag} -->`;
    const apiBase = `https://api.github.com/repos/${repo}`;
    const headers = {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'User-Agent': 'github-actions-security-report',
      'X-GitHub-Api-Version': '2022-11-28'
    };

    try {
      const commentsRes = await fetch(`${apiBase}/issues/${prNumber}/comments?per_page=100`, { headers });
      if (!commentsRes.ok) {
        console.warn(`Failed to list comments: HTTP ${commentsRes.status}`);
      } else {
        const comments = await commentsRes.json();
        const existingComment = comments.find((c) => c.body?.includes(marker));

        if (existingComment) {
          const updateRes = await fetch(`${apiBase}/issues/comments/${existingComment.id}`, {
            method: 'PATCH',
            headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ body: md })
          });
          if (updateRes.ok) {
            console.log(`Updated existing PR comment #${existingComment.id}`);
          } else {
            console.warn(`Failed to update PR comment: HTTP ${updateRes.status}`);
          }
        } else {
          const createRes = await fetch(`${apiBase}/issues/${prNumber}/comments`, {
            method: 'POST',
            headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ body: md })
          });
          if (createRes.ok) {
            console.log(`Created new PR comment on #${prNumber}`);
          } else {
            console.warn(`Failed to create PR comment: HTTP ${createRes.status}`);
          }
        }
      }
    } catch (apiErr) {
      console.warn(`Error during PR comment upsert: ${apiErr.message}`);
    }
  } else {
    console.log('Skipping PR comment: Not a PR event or missing GITHUB_TOKEN/GITHUB_REPOSITORY.');
  }

  if (shouldManageIssue && token && repo) {
    const apiBase = `https://api.github.com/repos/${repo}`;
    const headers = {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'User-Agent': 'github-actions-security-report',
      'X-GitHub-Api-Version': '2022-11-28'
    };

    try {
      const listRes = await fetch(`${apiBase}/issues?state=open&labels=automated-audit`, { headers });
      if (!listRes.ok) {
        console.warn(`Failed to list issues for audit: HTTP ${listRes.status}`);
      } else {
        const issues = await listRes.json();
        const existingIssue = issues.find((i) => i.title.includes('[Security Audit]'));

        const runUrl = process.env.GITHUB_SERVER_URL && process.env.GITHUB_RUN_ID
          ? `${process.env.GITHUB_SERVER_URL}/${repo}/actions/runs/${process.env.GITHUB_RUN_ID}`
          : '';
        const body = `## Automated Security Audit Alert\n\n${md}\n\n---\n*Run: [${process.env.GITHUB_RUN_ID || 'Workflow Run'}](${runUrl})*`;

        if (total > 0) {
          if (existingIssue) {
            const updateRes = await fetch(`${apiBase}/issues/${existingIssue.number}`, {
              method: 'PATCH',
              headers: { ...headers, 'Content-Type': 'application/json' },
              body: JSON.stringify({ body })
            });
            if (updateRes.ok) console.log(`Updated open issue #${existingIssue.number}`);
          } else {
            const createRes = await fetch(`${apiBase}/issues`, {
              method: 'POST',
              headers: { ...headers, 'Content-Type': 'application/json' },
              body: JSON.stringify({
                title: issueTitle,
                body,
                labels: ['security', 'automated-audit']
              })
            });
            if (createRes.ok) {
              const created = await createRes.json();
              console.log(`Created new issue #${created.number}`);
            }
          }
        } else if (existingIssue) {
          await fetch(`${apiBase}/issues/${existingIssue.number}/comments`, {
            method: 'POST',
            headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ body: '✅ **Resolved**: The latest scheduled security audit detected 0 vulnerabilities. Closing issue.' })
          });
          await fetch(`${apiBase}/issues/${existingIssue.number}`, {
            method: 'PATCH',
            headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ state: 'closed' })
          });
          console.log(`Closed resolved issue #${existingIssue.number}`);
        }
      }
    } catch (issueErr) {
      console.warn(`Error during audit issue management: ${issueErr.message}`);
    }
  }

  if (failOnFindings && total > 0) {
    console.error(`Failing build due to ${total} security finding(s).`);
    process.exit(1);
  }
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
