import './globals.css';

export const metadata = {
  title: 'InboxRadar — AI Email Reading Agent',
  description: 'AI-powered real-time email reading, classification, priority tracking and instant alerts.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="icon" href="https://i.postimg.cc/NFf39kf7/99bf8e7b-fc1e-478a-9f0a-d5b4d34b58d4-removebg-preview.png" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
