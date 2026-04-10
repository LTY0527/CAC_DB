import PublicWorkspace from './PublicWorkspace'

export default function RoleWorkspace({ employmentData = [], dataLoadedAt = '' }) {
  return <PublicWorkspace employmentData={employmentData} dataLoadedAt={dataLoadedAt} />
}
