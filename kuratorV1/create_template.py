import os

# Ensure templates directory exists
os.makedirs('templates', exist_ok=True)

# Create index.html
index_html = """<!DOCTYPE html>
<html data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Empire IV - Discord Bot</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
</head>
<body>
    <div class="container my-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card bg-dark">
                    <div class="card-header bg-secondary text-white">
                        <h2 class="text-center">Empire IV - Diplomacy Bot</h2>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-success">
                            <h4 class="alert-heading">Bot Status: Online</h4>
                            <p>The Discord bot is currently running and ready to manage diplomatic affairs.</p>
                        </div>
                        <h5 class="mt-4">Available Features:</h5>
                        <ul class="list-group list-group-flush mb-4">
                            <li class="list-group-item bg-dark text-light">Moderation Commands</li>
                            <li class="list-group-item bg-dark text-light">Trade Agreements</li>
                            <li class="list-group-item bg-dark text-light">Diplomatic Treaties</li>
                            <li class="list-group-item bg-dark text-light">Country Development</li>
                        </ul>
                        <div class="text-center">
                            <p>This web server keeps the bot alive 24/7.</p>
                        </div>
                    </div>
                    <div class="card-footer text-center text-muted">
                        Empire IV Diplomacy Bot &copy; 2023
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""

# Write the file
with open('templates/index.html', 'w') as f:
    f.write(index_html)

print("Template created successfully.")