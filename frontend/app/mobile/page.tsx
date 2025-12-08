'use client';

import { Wine, Smartphone, Apple, Globe, Share2 } from 'lucide-react';
import Link from 'next/link';

export default function MobilePage() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="text-center mb-8">
        <div className="p-4 bg-amber-100 rounded-full w-fit mx-auto mb-4">
          <Smartphone className="h-12 w-12 text-amber-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Use on Your Phone
        </h1>
        <p className="text-gray-600">
          Multiple ways to share cocktail recipe screenshots from your phone
        </p>
      </div>

      <div className="space-y-6">
        {/* Option 1: Direct Access */}
        <div className="card p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Globe className="h-6 w-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Option 1: Open in Phone Browser
              </h2>
              <p className="text-gray-600 text-sm mb-4">
                The easiest way - just open this app on your phone's browser.
              </p>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm font-mono text-gray-700 mb-2">
                  On your phone, open Safari/Chrome and go to:
                </p>
                <code className="block bg-white p-3 rounded border text-sm break-all">
                  http://YOUR_COMPUTER_IP:3000/upload
                </code>
                <p className="text-xs text-gray-500 mt-2">
                  (Your computer and phone must be on the same WiFi network)
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Option 2: Add to Home Screen */}
        <div className="card p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-amber-100 rounded-lg">
              <Share2 className="h-6 w-6 text-amber-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Option 2: Add to Home Screen (PWA)
              </h2>
              <p className="text-gray-600 text-sm mb-4">
                Install as an app for quicker access. On Android, this also enables sharing directly to the app.
              </p>
              <div className="space-y-3 text-sm">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="font-medium text-gray-900 mb-2">iOS (Safari):</p>
                  <ol className="list-decimal list-inside space-y-1 text-gray-600">
                    <li>Open the app in Safari</li>
                    <li>Tap the Share button (square with arrow)</li>
                    <li>Scroll down and tap "Add to Home Screen"</li>
                  </ol>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="font-medium text-gray-900 mb-2">Android (Chrome):</p>
                  <ol className="list-decimal list-inside space-y-1 text-gray-600">
                    <li>Open the app in Chrome</li>
                    <li>Tap the menu (3 dots)</li>
                    <li>Tap "Add to Home screen" or "Install app"</li>
                  </ol>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Option 3: iOS Shortcut */}
        <div className="card p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-gray-100 rounded-lg">
              <Apple className="h-6 w-6 text-gray-700" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Option 3: iOS Shortcut (Advanced)
              </h2>
              <p className="text-gray-600 text-sm mb-4">
                Create a shortcut that uploads images directly from the share sheet.
              </p>
              <div className="bg-gray-50 rounded-lg p-4 text-sm">
                <p className="font-medium text-gray-900 mb-2">Create this Shortcut:</p>
                <ol className="list-decimal list-inside space-y-2 text-gray-600">
                  <li>Open the Shortcuts app on your iPhone</li>
                  <li>Tap + to create a new shortcut</li>
                  <li>Add action: "Get Images from Input"</li>
                  <li>Add action: "Get Contents of URL"
                    <ul className="list-disc list-inside ml-4 mt-1">
                      <li>URL: <code className="bg-white px-1 rounded">http://YOUR_IP:8000/api/upload/extract-immediate</code></li>
                      <li>Method: POST</li>
                      <li>Request Body: Form</li>
                      <li>Add field: file (File, from previous action)</li>
                    </ul>
                  </li>
                  <li>Add action: "Show Result"</li>
                  <li>Tap the shortcut name → "Show in Share Sheet"</li>
                  <li>Select "Images" as accepted type</li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8 text-center">
        <Link href="/upload" className="btn btn-primary">
          Go to Upload Page
        </Link>
      </div>
    </div>
  );
}
