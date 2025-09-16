import { getSignedUrl, publicClient } from "~/configuration/client"

/**
 * Uploads file to Azure Blob Storage. Each storage provider has a slightly different API
 * so you'll need to implement this for your specific provider.
 */
async function uploadToAzureBlob(file: File, signedUrl: string) {
  const uploadResponse = await fetch(signedUrl, {
    method: "PUT",
    body: file,
    headers: {
      "x-ms-blob-type": "BlockBlob",
      "Content-Type": file.type,
    },
  })

  if (!uploadResponse.ok) {
    const error = {
      message: `File upload failed with status ${uploadResponse.status}`,
    }

    return { data: null, error }
  }

  return { data: signedUrl, error: null }
}

/**
 * Uploads a file to Azure Blob Storage via SAS token
 *
 * @param file - File object to upload (typically from React Hook Form)
 * @param options - Upload options (currently unused)
 * @returns Promise resolving to [data, error] tuple
 */
export async function uploadFile(file: File) {
  const { data: blobUrls, error: getSignedUrlError } = await getSignedUrl({
    client: publicClient,
    body: {
      file_name: file.name,
    },
  })

  if (getSignedUrlError) {
    return { data: null, error: getSignedUrlError }
  }

  const { signed_url: signedUrl, public_url: publicUrl } = blobUrls

  // Step 2: Upload file to Azure Blob Storage
  const { data: _uploadedData, error } = await uploadToAzureBlob(
    file,
    signedUrl,
  )

  if (error) {
    return { data: null, error }
  }

  return { data: publicUrl, error: null }
}
