import React from "react";

export default function EmailDashboard() {
  return (
    <main className="p-8 max-w-5xl mx-auto font-sans">
      <h1 className="text-3xl font-bold mb-2">Email Automation & Reminder Dashboard</h1>
      <p className="text-gray-600 mb-6">Manage contacts, Jinja2 templates, recurring RRULE reminders, and delivery logs.</p>
      <div className="border rounded-lg p-4 bg-white shadow-sm">
        <p className="text-sm text-gray-500">Connect to FastAPI endpoint <code>GET /logs</code> to inspect dispatch statuses.</p>
      </div>
    </main>
  );
}
