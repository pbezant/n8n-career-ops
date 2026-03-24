/**
 * setup-google-sheet.js
 * One-off script to create the Career-Ops Dashboard Google Sheet.
 * Run once: npm run setup-sheet
 * Copy the printed Spreadsheet ID into your n8n Google Sheets nodes.
 */

require('dotenv').config();
const { google } = require('googleapis');
const fs = require('fs');

const KEY_PATH = process.env.GOOGLE_SERVICE_ACCOUNT_KEY_PATH || './service-account-key.json';
const SHEET_NAME = process.env.GOOGLE_SHEETS_SPREADSHEET_NAME || 'Career-Ops Dashboard';

async function main() {
  const key = JSON.parse(fs.readFileSync(KEY_PATH, 'utf8'));
  const auth = new google.auth.GoogleAuth({
    credentials: key,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });
  const sheets = google.sheets({ version: 'v4', auth });

  // --- Create the spreadsheet with all tabs ---
  const createRes = await sheets.spreadsheets.create({
    requestBody: {
      properties: { title: SHEET_NAME },
      sheets: [
        { properties: { title: 'Pipeline', sheetId: 0 } },
        { properties: { title: 'Evaluations', sheetId: 1 } },
        { properties: { title: 'Applications', sheetId: 2 } },
        { properties: { title: 'Config', sheetId: 3 } },
        { properties: { title: 'Comparisons', sheetId: 4 } },
        { properties: { title: 'Archive', sheetId: 5 } },
        { properties: { title: 'Logs', sheetId: 6 } },
      ],
    },
  });

  const spreadsheetId = createRes.data.spreadsheetId;
  console.log('\n✅ Spreadsheet created!');
  console.log(`📋 Spreadsheet ID: ${spreadsheetId}`);
  console.log(`🔗 URL: https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit\n`);

  // --- Write headers ---
  const headers = {
    Pipeline: [['ID', 'Source', 'Company', 'Title', 'URL', 'JD Snippet', 'Date Found', 'Freshness Hours', 'Status', 'Dedup Key']],
    Evaluations: [['Job ID', 'Overall Score', 'Grade', 'Role Match', 'Skills', 'Seniority', 'Compensation', 'Geographic', 'Company Stage', 'Product-Market', 'Growth', 'Interview Likelihood', 'Timeline', 'Freshness Adjusted Score', 'Executive Summary', 'CV Match', 'Gaps', 'Archetype', 'Full Report', 'Confidence']],
    Applications: [['Job ID', 'Applied Date', 'CV HTML', 'CV PDF Link', 'Cover Letter', 'Pre-filled Answers JSON', 'Interview Prep', 'Status', 'Follow-up Date', 'Notes', 'CV Version']],
    Config: [
      ['Key', 'Value'],
      ['job_titles', 'Product Designer,UX Designer,IoT Engineer,Creative Technologist,Front End Developer'],
      ['locations', 'remote,Austin TX'],
      ['salary_min', '120000'],
      ['salary_max', '180000'],
      ['remote_preference', 'remote_first'],
      ['score_threshold', '4.0'],
      ['scan_budget_daily', '200'],
      ['generate_pdf', 'false'],
      ['scan_frequency', 'daily'],
      ['cse_engine_id', 'YOUR_CSE_ENGINE_ID'],
      ['eeo_race', 'Prefer not to say'],
      ['eeo_gender', 'Male'],
      ['eeo_veteran', 'No'],
      ['eeo_disability', 'No'],
      ['eeo_hispanic', 'No'],
    ],
    Comparisons: [['Comparison ID', 'Job IDs', 'Ranking', 'Analysis', 'Date']],
    Archive: [['ID', 'Source', 'Company', 'Title', 'URL', 'Date Found', 'Status', 'Archive Date', 'Archive Reason']],
    Logs: [['Timestamp', 'Workflow', 'Level', 'Message', 'Job ID', 'Details']],
  };

  const batchData = Object.entries(headers).map(([sheetTitle, values]) => ({
    range: `${sheetTitle}!A1`,
    values,
  }));

  await sheets.spreadsheets.values.batchUpdate({
    spreadsheetId,
    requestBody: { valueInputOption: 'RAW', data: batchData },
  });

  // --- Formatting: bold headers, freeze row 1, conditional formatting on Grade ---
  const formatRequests = [
    // Bold header row in all sheets
    ...[0, 1, 2, 3, 4, 5, 6].map((sheetId) => ({
      repeatCell: {
        range: { sheetId, startRowIndex: 0, endRowIndex: 1 },
        cell: { userEnteredFormat: { textFormat: { bold: true }, backgroundColor: { red: 0.9, green: 0.9, blue: 0.9 } } },
        fields: 'userEnteredFormat(textFormat,backgroundColor)',
      },
    })),
    // Freeze row 1 in Pipeline tab
    { updateSheetProperties: { properties: { sheetId: 0, gridProperties: { frozenRowCount: 1 } }, fields: 'gridProperties.frozenRowCount' } },
    // Freeze row 1 in Evaluations tab
    { updateSheetProperties: { properties: { sheetId: 1, gridProperties: { frozenRowCount: 1 } }, fields: 'gridProperties.frozenRowCount' } },
    // Conditional formatting: Grade A = green, B = blue, C = yellow, D/F = red (Evaluations col C = index 2)
    {
      addConditionalFormatRule: {
        rule: {
          ranges: [{ sheetId: 1, startColumnIndex: 2, endColumnIndex: 3 }],
          booleanRule: { condition: { type: 'TEXT_EQ', values: [{ userEnteredValue: 'A' }] }, format: { backgroundColor: { red: 0.56, green: 0.93, blue: 0.56 } } },
        },
        index: 0,
      },
    },
    {
      addConditionalFormatRule: {
        rule: {
          ranges: [{ sheetId: 1, startColumnIndex: 2, endColumnIndex: 3 }],
          booleanRule: { condition: { type: 'TEXT_EQ', values: [{ userEnteredValue: 'B' }] }, format: { backgroundColor: { red: 0.68, green: 0.85, blue: 1.0 } } },
        },
        index: 1,
      },
    },
    {
      addConditionalFormatRule: {
        rule: {
          ranges: [{ sheetId: 1, startColumnIndex: 2, endColumnIndex: 3 }],
          booleanRule: { condition: { type: 'TEXT_EQ', values: [{ userEnteredValue: 'C' }] }, format: { backgroundColor: { red: 1.0, green: 0.95, blue: 0.6 } } },
        },
        index: 2,
      },
    },
    {
      addConditionalFormatRule: {
        rule: {
          ranges: [{ sheetId: 1, startColumnIndex: 2, endColumnIndex: 3 }],
          booleanRule: {
            condition: { type: 'CUSTOM_FORMULA', values: [{ userEnteredValue: '=OR(C2="D",C2="F")' }] },
            format: { backgroundColor: { red: 1.0, green: 0.7, blue: 0.7 } },
          },
        },
        index: 3,
      },
    },
  ];

  await sheets.spreadsheets.batchUpdate({ spreadsheetId, requestBody: { requests: formatRequests } });

  console.log('✅ Headers written and formatting applied.');
  console.log('\n📌 Next steps:');
  console.log(`   1. Copy the Spreadsheet ID above`);
  console.log(`   2. In each n8n workflow, update the Google Sheets nodes to use this ID`);
  console.log(`   3. Update the Config tab with your actual CSE Engine ID`);
  console.log(`   4. Share the sheet with your Google Sheets OAuth2 account email in n8n\n`);
}

main().catch((err) => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});
