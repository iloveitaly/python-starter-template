import { publicClient } from "~/configuration/client"

/**
 * Mocked function to retrieve a signed URL for file uploads.
 *
 * NOTE: This is a placeholder and MUST be implemented on the backend to provide
 * secure, time-limited access to your storage provider (e.g., S3, Google Cloud Storage).
 * The backend implementation should verify the user's permissions and return a valid signed URL.
 */
const getSignedUrl = async (_args: any): Promise<any> => {
  console.warn("getSignedUrl called. This is a mock implementation.")
  return {
    data: {
      signed_url: "https://storage.example.com/mock-signed-url",
      public_url: "https://storage.example.com/mock-public-url",
    },
    error: null,
  }
}

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
