Write-Host "Creating model directory..."
$dest = "C:\Users\Ayoola\Downloads\greenlight\data\all-MiniLM-L6-v2"
New-Item -ItemType Directory -Force -Path "$dest"
New-Item -ItemType Directory -Force -Path "$dest\1_Pooling"

$base = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main"

$files = @(
    "config.json",
    "tokenizer_config.json",
    "tokenizer.json",
    "vocab.txt",
    "special_tokens_map.json",
    "modules.json",
    "sentence_bert_config.json",
    "model.safetensors"
)

foreach ($f in $files) {
    Write-Host "Downloading $f..."
    Invoke-WebRequest -Uri "$base/$f" -OutFile "$dest\$f"
    Write-Host "  Done: $f"
}

Write-Host "Downloading 1_Pooling/config.json..."
Invoke-WebRequest -Uri "$base/1_Pooling/config.json" -OutFile "$dest\1_Pooling\config.json"

Write-Host ""
Write-Host "All files downloaded! Model ready at: $dest"
