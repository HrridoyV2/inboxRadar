import './globals.css';

export const metadata = {
  title: 'InboxRadar AI — Intelligent Email Categorization',
  description: 'AI-powered real-time email reading, classification, priority tracking and instant alerts.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
