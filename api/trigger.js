export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  const result = await fetch(
    'https://api.github.com/repos/morussoHALOS/heatmapHALOS/actions/workflows/update.yml/dispatches',
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.GH_PAT}`,
        Accept: 'application/vnd.github+json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ref: 'main',
      }),
    }
  );

  if (result.ok) {
    res.status(200).json({ message: '✅ GitHub Action triggered!' });
  } else {
    const errorText = await result.text();
    res.status(result.status).json({ error: errorText });
  }
}
